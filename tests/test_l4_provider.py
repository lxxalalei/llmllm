from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.knowledge.behavior_rules import BehaviorRule, RuleConditions
from app.knowledge.l4_compiler import L4Draft, L4IntentBrief, L4Plan
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus

from app.llm import l4_provider


class FakeResponses:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.outputs.pop(0))


class FakeAsyncOpenAI:
    instances: list["FakeAsyncOpenAI"] = []

    def __init__(self, **kwargs: object) -> None:
        self.init_kwargs = kwargs
        self.responses = FakeResponses([])
        self.closed = False
        self.__class__.instances.append(self)

    async def close(self) -> None:
        self.closed = True


def _rule(rule_id: str, *, action: str = "add_member") -> BehaviorRule:
    return BehaviorRule(
        id=rule_id,
        title="成员操作规则",
        domain="channel",
        capability="membership",
        actor="requester",
        action=action,
        resource="channel",
        conditions=RuleConditions(),
        decision="allow_when_evidence_matches",
        source_fact_ids=[f"eng.{rule_id.removeprefix('rule.')}.fact"],
    )


def _existing_item(knowledge_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title="已有 FAQ",
        layer=KnowledgeLayer.L4_USER_KNOWLEDGE,
        module="mattermost.channel",
        feature="channel_membership",
        content="已有内容只用于判断是否重复。",
        status=KnowledgeStatus.DRAFT,
    )


def _brief(rule_ids: list[str]) -> L4IntentBrief:
    return L4IntentBrief(
        id="faq.mattermost.channel.membership.self_vs_other",
        question="为什么自己能加入但不能添加别人？",
        question_variants=["自己加入和添加别人有什么区别？"],
        candidate_rule_ids=rule_ids,
        existing_knowledge_ids=["faq.existing"]
    )


def _composer(monkeypatch: pytest.MonkeyPatch, outputs: list[str]):
    fake = FakeAsyncOpenAI()
    fake.responses = FakeResponses(outputs)

    def build_fake(**kwargs: object) -> FakeAsyncOpenAI:
        fake.init_kwargs = kwargs
        return fake

    monkeypatch.setattr(l4_provider, "AsyncOpenAI", build_fake)
    composer = l4_provider.OpenAIL4Composer(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        reasoning_effort="high",
    )
    return composer, fake


def test_l4_composer_runs_plan_write_review_with_runtime_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = _rule("rule.channel.membership.self")
    outputs = [
        '{"action":"create","rule_ids":["rule.channel.membership.self"],'
        '"merge_ids":[],"rationale":"问题有独立解释价值。","missing_evidence":[]}',
        '{"answer":"自己加入与添加别人使用的权限判断不同。"}',
        '{"issues":[],"missing_evidence":[]}',
    ]
    composer, fake = _composer(monkeypatch, outputs)
    brief = _brief([rule.id])
    spec_reads = 0
    original_load_spec = l4_provider._load_authoring_spec

    def load_spec() -> str:
        nonlocal spec_reads
        spec_reads += 1
        return original_load_spec()

    monkeypatch.setattr(l4_provider, "_load_authoring_spec", load_spec)

    async def run() -> tuple[object, object, object]:
        plan = await composer.plan(
            brief=brief,
            rules=[rule],
            existing_items=[_existing_item("faq.existing")],
        )
        draft = await composer.write(brief=brief, plan=plan, rules=[rule])
        review = await composer.review(brief=brief, draft=draft, rules=[rule])
        return plan, draft, review

    plan, draft, review = asyncio.run(run())

    assert plan.action == "create"
    assert draft.answer.startswith("自己加入")
    assert review.issues == []
    assert fake.init_kwargs == {
        "api_key": "test-key",
        "base_url": "https://example.test/v1",
    }
    assert len(fake.responses.calls) == 3
    assert all(
        call["reasoning"] == {"effort": "high"}
        for call in fake.responses.calls
    )
    assert spec_reads == 3

    spec_path = Path(l4_provider.__file__).resolve().parent / "prompts" / "l4_authoring.md"
    spec_marker = spec_path.read_text(encoding="utf-8").splitlines()[0]
    assert all(spec_marker in str(call["instructions"]) for call in fake.responses.calls)
    assert "PLAN" in str(fake.responses.calls[0]["instructions"])
    assert "WRITE" in str(fake.responses.calls[1]["instructions"])
    assert "REVIEW" in str(fake.responses.calls[2]["instructions"])


def test_write_only_sends_selected_rules_and_review_receives_draft_and_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _rule("rule.channel.membership.self")
    unselected = _rule("rule.channel.membership.other", action="add_other")
    outputs = [
        '{"answer":"用户需要区分自己与他人的操作。"}',
        '{"issues":["缺少具体权限名称"],"missing_evidence":["权限名称"]}',
    ]
    composer, fake = _composer(monkeypatch, outputs)
    brief = _brief([selected.id])
    plan = L4Plan(
        action="create",
        rule_ids=[selected.id],
        merge_ids=[],
        rationale="selected",
        missing_evidence=[],
    )

    async def run() -> tuple[L4Draft, object]:
        draft = await composer.write(
            brief=brief,
            plan=plan,
            rules=[selected, unselected],
        )
        review = await composer.review(brief=brief, draft=draft, rules=[selected])
        return draft, review

    draft, review = asyncio.run(run())

    assert review.issues == ["缺少具体权限名称"]
    assert "资料不足" not in draft.answer
    write_input = str(fake.responses.calls[0]["input"])
    assert selected.id in write_input
    assert unselected.id not in write_input
    review_input = str(fake.responses.calls[1]["input"])
    assert "用户需要区分自己与他人的操作。" in review_input
    assert selected.id in review_input
    assert "缺少具体权限名称" not in review_input
    assert "AUTHORITATIVE BEHAVIOR RULE EVIDENCE" in review_input
    write_instructions = str(fake.responses.calls[0]["instructions"])
    review_instructions = str(fake.responses.calls[1]["instructions"])
    assert "核心问题无法回答" in write_instructions
    assert "外围操作或配置细节缺少证据" in write_instructions
    assert "不要在答案正文中写通用的‘资料不足’模板" in write_instructions
    assert "外围操作或配置细节缺少证据" in review_instructions


@pytest.mark.parametrize(
    ("method_name", "expected_error"),
    [
        ("plan", "no structured L4 plan"),
        ("write", "no structured L4 draft"),
        ("review", "no structured L4 review"),
    ],
)
def test_l4_composer_rejects_missing_structured_output(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
    expected_error: str,
) -> None:
    rule = _rule("rule.channel.membership.self")
    composer, _fake = _composer(monkeypatch, [""])
    brief = _brief([rule.id])
    plan = L4Plan(
        action="create",
        rule_ids=[rule.id],
        merge_ids=[],
        rationale="selected",
        missing_evidence=[],
    )

    async def run() -> object:
        if method_name == "plan":
            return await composer.plan(brief=brief, rules=[rule], existing_items=[])
        if method_name == "write":
            return await composer.write(brief=brief, plan=plan, rules=[rule])
        return await composer.review(
            brief=brief,
            draft=L4Draft(answer="草稿"),
            rules=[rule],
        )

    with pytest.raises(ValueError, match=expected_error):
        asyncio.run(run())


def test_l4_composer_close_closes_openai_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composer, fake = _composer(monkeypatch, [])

    asyncio.run(composer.close())

    assert fake.closed
