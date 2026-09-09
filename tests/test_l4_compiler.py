import pytest

from app.knowledge.assets import KnowledgeCatalog
from app.knowledge.behavior_rules import BehaviorRule
from app.knowledge.models import KnowledgeItem, KnowledgeStatus
from app.knowledge.l4_compiler import (
    L4IntentBrief, L4IntentManifest, L4Plan, L4Draft, L4Review, compile_l4_preview,
)


def inputs():
    fact = KnowledgeItem(id="fact.demo.create", title="fact", layer="L1", module="demo", feature="creation", content="fact", status="review", sources=[{"repo": "demo", "file": "create.py", "symbol": "create"}])
    rule = BehaviorRule(id="rule.demo.create", title="creation", domain="demo", capability="create", actor="user", action="create", resource="channel", decision="permission required", source_fact_ids=[fact.id])
    view = KnowledgeItem(id="product.demo.create", title="product", layer="L3", module="demo", feature="creation", content="permission required", status="review", behavior_rule_id=rule.id, derived_from=[fact.id])
    old = KnowledgeItem(id="faq.demo.old", title="old", layer="L4", module="demo", feature="creation", content="old", status="published", visible_roles=["user"])
    brief = L4IntentBrief(id="faq.demo.create", question="Why can't I create?", question_variants=["Why is creation blocked?"], candidate_rule_ids=[rule.id], existing_knowledge_ids=[old.id])
    return KnowledgeCatalog([fact, view, old]), [rule], L4IntentManifest(module="demo", feature="creation", intents=[brief])


class Composer:
    def __init__(self, action="merge", issues=None):
        self.action = action
        self.issues = issues or []
        self.calls = []
        self.rule_ids = ["rule.demo.create"]

    async def plan(self, **kwargs):
        self.calls.append(("plan", kwargs))
        return L4Plan(action=self.action, rule_ids=self.rule_ids, merge_ids=["faq.demo.old"] if self.action == "merge" else [], rationale="one intent", missing_evidence=["UI setting path"] if self.action == "gap" else [])

    async def write(self, **kwargs):
        self.calls.append(("write", kwargs))
        return L4Draft(answer="Creating this channel requires the matching permission.")

    async def review(self, **kwargs):
        self.calls.append(("review", kwargs))
        return L4Review(issues=self.issues, missing_evidence=[])


@pytest.mark.asyncio
async def test_merge_proposes_one_draft_without_mutating_existing_knowledge():
    catalog, rules, manifest = inputs()
    model = Composer(issues=["explain which permission"])
    result = await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    candidate = result.candidates[0]
    assert candidate.item.status == KnowledgeStatus.DRAFT
    assert candidate.item.layer == "L4"
    assert candidate.item.derived_from == ["product.demo.create"]
    assert candidate.item.behavior_rule_ids == [rules[0].id]
    assert candidate.item.question_variants == manifest.intents[0].question_variants
    assert candidate.review.issues == ["explain which permission"]
    assert catalog.get("faq.demo.old").content == "old"
    assert catalog.get("faq.demo.old").status == "published"
    assert [name for name, _ in model.calls] == ["plan", "write", "review"]
    assert model.calls[1][1]["rules"] == rules


@pytest.mark.asyncio
async def test_evidence_gap_skips_writer_and_reviewer():
    catalog, rules, manifest = inputs()
    model = Composer(action="gap")
    result = await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    assert result.candidates[0].item is None
    assert result.candidates[0].review is None
    assert [name for name, _ in model.calls] == ["plan"]


@pytest.mark.asyncio
async def test_invented_rule_is_rejected_before_writing():
    catalog, rules, manifest = inputs()
    model = Composer()
    model.rule_ids = ["rule.demo.invented"]
    with pytest.raises(ValueError, match="rule"):
        await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    assert [name for name, _ in model.calls] == ["plan"]


@pytest.mark.asyncio
@pytest.mark.parametrize("defect", ["scope", "missing_fact", "unreviewed_fact", "missing_view", "duplicate_intent", "undeclared_target"])
async def test_invalid_inputs_rejected_before_any_model_call(defect):
    catalog, rules, manifest = inputs()
    if defect == "scope":
        rules[0].domain = "other"
    elif defect == "missing_fact":
        rules[0].source_fact_ids = ["fact.missing"]
    elif defect == "unreviewed_fact":
        catalog.get("fact.demo.create").status = KnowledgeStatus.DRAFT
    elif defect == "missing_view":
        del catalog._items["product.demo.create"]
    elif defect == "duplicate_intent":
        manifest.intents.append(manifest.intents[0])
    else:
        manifest.intents[0].id = "faq.demo.old"
        manifest.intents[0].existing_knowledge_ids = []
    model = Composer()
    with pytest.raises(ValueError):
        await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    assert not model.calls


@pytest.mark.asyncio
async def test_two_intents_cannot_replace_the_same_existing_faq():
    catalog, rules, manifest = inputs()
    manifest.intents.append(manifest.intents[0].model_copy(update={"id": "faq.demo.second"}))
    model = Composer()
    with pytest.raises(ValueError, match="merge"):
        await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    assert all(name == "plan" for name, _ in model.calls)


@pytest.mark.asyncio
async def test_create_passes_only_selected_evidence_to_writer_and_reviewer():
    catalog, rules, manifest = inputs()
    other = rules[0].model_copy(update={"id": "rule.demo.other"})
    view = catalog.get("product.demo.create").model_copy(update={"id": "product.demo.other", "behavior_rule_id": other.id})
    catalog._items[view.id] = view
    rules.append(other)
    manifest.intents[0].candidate_rule_ids.append(other.id)
    model = Composer(action="create")
    result = await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=model)
    candidate = result.candidates[0]
    assert candidate.item.status == "draft"
    assert candidate.review.issues == []
    assert candidate.item.behavior_rule_ids == [rules[0].id]
    assert [r.id for r in model.calls[0][1]["rules"]] == [r.id for r in rules]
    for _, kwargs in model.calls[1:]:
        assert [r.id for r in kwargs["rules"]] == [rules[0].id]


@pytest.mark.parametrize("changes", [
    {"action": "create", "merge_ids": ["faq.demo.old"]},
    {"action": "merge", "merge_ids": []},
    {"merge_ids": ["faq.other"]},
    {"rule_ids": []},
    {"rule_ids": ["rule.demo.create", "rule.demo.create"]},
    {"action": "gap", "missing_evidence": [], "merge_ids": []},
    {"action": "gap", "missing_evidence": ["  "], "merge_ids": []},
    {"action": "gap", "missing_evidence": ["missing UI"]},
])
def test_invalid_merge_and_gap_proposals_cannot_be_used(changes):
    from app.knowledge.l4_compiler import validate_l4_plan

    catalog, _, manifest = inputs()
    plan = L4Plan(action="merge", rule_ids=["rule.demo.create"], merge_ids=["faq.demo.old"], rationale="same intent", missing_evidence=[]).model_copy(update=changes)
    with pytest.raises(ValueError):
        validate_l4_plan(brief=manifest.intents[0], plan=plan, catalog=catalog)


@pytest.mark.asyncio
async def test_real_composer_interface_compiles_three_fake_api_responses(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from app.llm import l4_provider

    catalog, rules, manifest = inputs()
    responses = AsyncMock(side_effect=[
        SimpleNamespace(output_text='{"action":"merge","rule_ids":["rule.demo.create"],"merge_ids":["faq.demo.old"],"rationale":"same user question","missing_evidence":[]}'),
        SimpleNamespace(output_text='{"answer":"Creation requires the matching permission."}'),
        SimpleNamespace(output_text='{"issues":[],"missing_evidence":["UI location is outside the supported answer"]}'),
    ])
    client = SimpleNamespace(responses=SimpleNamespace(create=responses), close=AsyncMock())
    monkeypatch.setattr(l4_provider, "AsyncOpenAI", lambda **kwargs: client)
    composer = l4_provider.OpenAIL4Composer(api_key="fake", model="fake")
    try:
        preview = await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=composer)
    finally:
        await composer.close()
    assert responses.await_count == 3
    assert preview.candidates[0].item.status == "draft"
    assert preview.candidates[0].item.content == "Creation requires the matching permission."
    assert preview.candidates[0].review.missing_evidence
    assert "UI location" not in preview.candidates[0].item.content
    client.close.assert_awaited_once()
