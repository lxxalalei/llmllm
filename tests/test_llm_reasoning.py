import asyncio
from types import SimpleNamespace

import pytest

from app.code_index import Symbol
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft
from app.knowledge.l2_generator import EngineeringRuleDraft
from app.knowledge.l2_generator import EngineeringRuleBatch
from app.knowledge.models import KnowledgeItem, KnowledgeLayer
from app.llm import (
    OpenAIEngineeringFactExtractor,
    OpenAIProductLogicExtractor,
    OpenAIUserKnowledgeExtractor,
)
from app.llm.openai_provider import (
    _parse_structured,
    _requires_upward_rule,
    _strip_json_fence,
)


class _FakeResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs):
        self.kwargs = kwargs
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text=(
                '{"facts":[{"key":"returns_flag","symbol":"is_enabled",'
                '"title":"Returns the supplied flag","statement":"The function returns flag."}]}'
            )
        )


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()

    async def close(self) -> None:
        return None


def test_engineering_fact_extractor_passes_reasoning_effort() -> None:
    extractor = OpenAIEngineeringFactExtractor(
        api_key="test",
        model="test-model",
        reasoning_effort="none",
    )
    fake_client = _FakeClient()
    extractor._client = fake_client

    result = asyncio.run(
        extractor.extract(
            [
                Symbol(
                    kind="function_definition",
                    name="is_enabled",
                    start_line=1,
                    end_line=1,
                    source="func is_enabled(flag bool) bool { return flag }",
                )
            ]
        )
    )

    assert len(result.facts) == 1
    assert len(fake_client.responses.calls) == 2
    assert all(
        call["reasoning"] == {"effort": "none"}
        for call in fake_client.responses.calls
    )
    instructions = fake_client.responses.calls[0]["instructions"]
    assert "Never emit both" in instructions
    assert "HARD LIMIT" in instructions
    review_instructions = fake_client.responses.calls[1]["instructions"]
    assert "permission check outside a self/non-self branch" in review_instructions
    assert "full complement" in review_instructions


class _QueuedResponses:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.outputs.pop(0))


class _QueuedClient:
    def __init__(self, outputs: list[str]) -> None:
        self.responses = _QueuedResponses(outputs)

    async def close(self) -> None:
        return None


def _knowledge_item(
    knowledge_id: str, layer: KnowledgeLayer, content: str
) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title="Rule",
        layer=layer,
        module="demo",
        feature="membership",
        content=content,
    )


def test_required_upward_rule_distinguishes_business_gates_from_http_mechanics() -> None:
    permission = _knowledge_item(
        "eng.demo.private_permission",
        KnowledgeLayer.L1_ENGINEERING_FACT,
        "Private-channel additions require PermissionManagePrivateChannelMembers.",
    )
    default_restriction = _knowledge_item(
        "eng.demo.default_restriction",
        KnowledgeLayer.L1_ENGINEERING_FACT,
        "Non-guest removal from the default channel is blocked.",
    )
    response_mechanics = _knowledge_item(
        "eng.demo.response",
        KnowledgeLayer.L1_ENGINEERING_FACT,
        "The handler returns the last error with HTTP 400 when no items succeed.",
    )

    assert _requires_upward_rule(permission)
    assert _requires_upward_rule(default_restriction)
    assert not _requires_upward_rule(response_mechanics)


def test_product_logic_extractor_uses_verified_result() -> None:
    l2_id = "eng.demo.private_permission"
    candidate = (
        '{"items":[{"key":"private_add","title":"Private add",'
        '"statement":"Only adding others requires permission.",'
        f'"derived_from":["{l2_id}"]}}]}}'
    )
    corrected = (
        '{"items":[{"key":"private_add","title":"Private add",'
        '"statement":"Every private-channel addition requires permission.",'
        f'"derived_from":["{l2_id}"]}}]}}'
    )
    extractor = OpenAIProductLogicExtractor(api_key="test", model="test")
    fake_client = _QueuedClient([candidate, corrected])
    extractor._client = fake_client

    result = asyncio.run(
        extractor.extract(
            [
                _knowledge_item(
                    l2_id,
                    KnowledgeLayer.L2_ENGINEERING_RULE,
                    "Private-channel additions require permission for every request.",
                )
            ]
        )
    )

    assert result.items[0].statement.startswith("Every")
    assert len(fake_client.responses.calls) == 2
    verifier = fake_client.responses.calls[1]["instructions"]
    assert "guest versus non-guest" in verifier
    assert "type-set completeness" in verifier


def test_user_knowledge_extractor_verifies_question_premise_and_answer() -> None:
    l3_id = "product.demo.default_channel"
    candidate = (
        '{"items":[{"key":"default_channel","question":"为什么访客不能移除？",'
        '"answer":"访客会被阻止。",'
        f'"derived_from":["{l3_id}"]}}]}}'
    )
    corrected = (
        '{"items":[{"key":"default_channel","question":"谁能从默认频道移除？",'
        '"answer":"仅访客允许执行该移除操作。",'
        f'"derived_from":["{l3_id}"]}}]}}'
    )
    extractor = OpenAIUserKnowledgeExtractor(api_key="test", model="test")
    fake_client = _QueuedClient([candidate, corrected])
    extractor._client = fake_client

    result = asyncio.run(
        extractor.extract(
            [
                _knowledge_item(
                    l3_id,
                    KnowledgeLayer.L3_PRODUCT_LOGIC,
                    "Default-channel removal is restricted to guests.",
                )
            ]
        )
    )

    assert result.items[0].question == "谁能从默认频道移除？"
    assert result.items[0].answer == "仅访客允许执行该移除操作。"
    assert len(fake_client.responses.calls) == 2
    verifier = fake_client.responses.calls[1]["instructions"]
    assert "QUESTION premise" in verifier
    assert "Never answer a reversed premise" in verifier


def test_generated_keys_normalize_symbol_casing_to_snake_case() -> None:
    fact = EngineeringFactDraft(
        key="AddUserToChannel_returnsExistingMember",
        symbol="AddUserToChannel",
        title="Returns existing member",
        statement="Returns an existing membership without creating another.",
    )
    rule = EngineeringRuleDraft(
        key="ChannelMembership_requiresTeamMembership",
        title="Team membership required",
        statement="Channel membership requires team membership.",
        derived_from=["eng.example.team_membership_check"],
    )

    assert fact.key == "add_user_to_channel_returns_existing_member"
    assert rule.key == "channel_membership_requires_team_membership"


def test_engineering_rule_batch_rejects_more_than_fifteen_rules() -> None:
    rules = [
        EngineeringRuleDraft(
            key=f"rule_{index}",
            title=f"Rule {index}",
            statement=f"Rule {index}.",
            derived_from=["eng.example.fact"],
        )
        for index in range(16)
    ]

    with pytest.raises(ValueError, match="too_long"):
        EngineeringRuleBatch(rules=rules)


def test_strip_json_fence_only_accepts_complete_json_wrapper() -> None:
    assert _strip_json_fence('```json\n{"facts": []}\n```') == '{"facts": []}'
    assert _strip_json_fence('```\n{"facts": []}\n```') == '{"facts": []}'
    assert _strip_json_fence('prefix\n```json\n{"facts": []}\n```') == (
        'prefix\n```json\n{"facts": []}\n```'
    )


def test_structured_parser_repairs_malformed_json_once() -> None:
    repaired = (
        '{"facts":[{"key":"valid_key","symbol":"Feature",'
        '"title":"Valid title","statement":"Valid statement."}]}'
    )
    fake_client = _QueuedClient([repaired])

    result = asyncio.run(
        _parse_structured(
            client=fake_client,
            model="test",
            reasoning_effort=None,
            value='{"facts":[{"key":"broken\nkey"}]}',
            model_type=EngineeringFactBatch,
            schema_name="repaired_facts",
        )
    )

    assert result.facts[0].key == "valid_key"
    assert len(fake_client.responses.calls) == 1
    assert "Preserve its meaning exactly" in fake_client.responses.calls[0]["instructions"]
