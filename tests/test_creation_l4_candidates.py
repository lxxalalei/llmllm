import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INTENT_PATH = ROOT / "config/knowledge_intents/mattermost-channel-creation.json"
PREVIEW_PATH = ROOT / "docs/baselines/creation-l4-preview-2026-09-08.json"
QA_PATH = ROOT / "config/qa_regression/creation-l4-2026-09-08.json"
RULE_ROOT = ROOT / "knowledge/behavior-rules/mattermost/channel-creation"
L3_ROOT = ROOT / "knowledge/l3-product-logic/mattermost/channel-creation"
L4_ROOT = ROOT / "knowledge/l4-user-knowledge/mattermost/channel-creation"

EXPECTED_INTENTS = {
    "faq.mattermost.channel.creation.channel_limit": {
        "rules": {"rule.mattermost.channel.creation.team_channel_limit"},
        "required_terms": {"频道数量上限", "超过", "拒绝"},
    },
    "faq.mattermost.channel.creation.create_permission_gate": {
        "rules": {
            "rule.mattermost.channel.creation.create_open_permission",
            "rule.mattermost.channel.creation.create_private_permission",
        },
        "required_terms": {"create_public_channel", "create_private_channel", "不代表"},
    },
    "faq.mattermost.channel.creation.creator_membership": {
        "rules": {"rule.mattermost.channel.creation.creator_membership"},
        "required_terms": {"成员", "管理员", "创建成功"},
    },
    "faq.mattermost.channel.creation.creation_side_effects": {
        "rules": {"rule.mattermost.channel.creation.creation_side_effects"},
        "required_terms": {"默认频道分类", "加入", "客户端"},
    },
    "faq.mattermost.channel.creation.discoverable_private_creation": {
        "rules": {"rule.mattermost.channel.creation.discoverable_private_creation"},
        "required_terms": {
            "私有频道",
            "启用",
            "manage_private_channel_discoverability",
            "必要",
        },
    },
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rule_ids() -> set[str]:
    return {
        yaml.safe_load(path.read_text(encoding="utf-8"))["id"]
        for path in RULE_ROOT.glob("*.yaml")
    }


def _l3_rule_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in L3_ROOT.glob("*.md"):
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        metadata = yaml.safe_load(frontmatter)
        if metadata.get("behavior_rule_id"):
            result[metadata["id"]] = metadata["behavior_rule_id"]
    return result


def _l4_ids() -> set[str]:
    result: set[str] = set()
    for path in L4_ROOT.glob("*.md"):
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        result.add(yaml.safe_load(frontmatter)["id"])
    return result


def test_creation_intent_manifest_has_five_non_atomic_user_intents() -> None:
    manifest = _load_json(INTENT_PATH)
    assert manifest["module"] == "mattermost.channel"
    assert manifest["feature"] == "channel_creation"

    intents = manifest["intents"]
    assert {intent["id"] for intent in intents} == set(EXPECTED_INTENTS)
    assert len(intents) == 5
    assert all(intent["question_variants"] for intent in intents)
    assert all(intent["candidate_rule_ids"] for intent in intents)
    assert all(intent["existing_knowledge_ids"] for intent in intents)
    assert all(
        intent["id"] in EXPECTED_INTENTS
        and set(intent["candidate_rule_ids"]) == EXPECTED_INTENTS[intent["id"]]["rules"]
        for intent in intents
    )
    assert len({intent["question"] for intent in intents}) == 5


def test_preview_candidates_are_draft_and_grounded_in_real_rules_and_l3() -> None:
    preview = _load_json(PREVIEW_PATH)
    assert preview["module"] == "mattermost.channel"
    assert preview["feature"] == "channel_creation"
    candidates = {candidate["item"]["id"]: candidate for candidate in preview["candidates"]}
    assert set(candidates) == set(EXPECTED_INTENTS)

    real_rule_ids = _rule_ids()
    l3_rule_map = _l3_rule_map()
    for candidate_id, expected in EXPECTED_INTENTS.items():
        candidate = candidates[candidate_id]
        intent = candidate["intent"]
        plan = candidate["plan"]
        item = candidate["item"]

        assert intent["id"] == candidate_id
        assert intent["question"] == item["title"]
        assert set(intent["candidate_rule_ids"]) == expected["rules"]
        assert intent["existing_knowledge_ids"]
        assert plan["action"] in {"create", "merge"}
        assert set(plan["rule_ids"]) == expected["rules"]
        assert set(plan["rule_ids"]) <= real_rule_ids
        assert item["status"] == "draft"
        assert item["id"] == candidate_id
        assert item["title"] == intent["question"]
        assert item["question_variants"] == intent["question_variants"]
        assert set(item["behavior_rule_ids"]) == set(plan["rule_ids"])
        assert set(item["visible_roles"]) == {
            "user",
            "product",
            "test",
            "developer",
            "admin",
        }
        assert set(item["derived_from"]) <= set(l3_rule_map)
        assert {
            l3_rule_map[l3_id] for l3_id in item["derived_from"]
        } == set(plan["rule_ids"])
        assert all(term in item["content"] for term in expected["required_terms"])
        assert "review" not in item["content"].lower()
        assert "缺口" not in item["content"]
        assert "证据" not in item["content"]
        assert candidate["review"] is not None
        assert candidate["review"]["issues"] == []
        assert isinstance(candidate["review"]["missing_evidence"], list)


def test_preview_merge_ids_are_existing_l4_only() -> None:
    manifest = _load_json(INTENT_PATH)
    preview = _load_json(PREVIEW_PATH)
    existing_l4_ids = _l4_ids()
    manifest_by_id = {intent["id"]: intent for intent in manifest["intents"]}

    for candidate in preview["candidates"]:
        candidate_id = candidate["item"]["id"]
        plan = candidate["plan"]
        assert set(plan["merge_ids"]) <= existing_l4_ids
        assert set(plan["merge_ids"]) <= set(manifest_by_id[candidate_id]["existing_knowledge_ids"])
        assert candidate["item"]["status"] == "draft"
        assert candidate_id in manifest_by_id
        assert candidate["intent"] == manifest_by_id[candidate_id]


def test_creation_l4_semantic_regression_cases_cover_claims_and_gaps() -> None:
    qa = _load_json(QA_PATH)
    assert qa["module"] == "mattermost.channel"
    assert qa["feature"] == "channel_creation"
    cases = qa["cases"]
    assert len(cases) >= 12
    assert len({case["id"] for case in cases}) == len(cases)

    candidate_ids = set(EXPECTED_INTENTS)
    assert all(case["expected_knowledge_id"] in candidate_ids | {None} for case in cases)
    assert all(case["required_claims"] for case in cases)
    assert all(case["forbidden_claims"] for case in cases)

    gap_cases = [case for case in cases if case["expected_gap"]]
    assert len(gap_cases) >= 3
    gap_questions = "\n".join(case["question"] for case in gap_cases)
    assert "具体" in gap_questions or "多少" in gap_questions
    assert "归档" in gap_questions
    assert any("设置" in case["question"] or "入口" in case["question"] for case in gap_cases)
    assert all(
        case["expected_knowledge_id"] is not None for case in gap_cases
    ), "gap cases should validate refusal after relevant retrieval, not a BM25 miss"


def test_limit_candidate_does_not_invent_operational_advice() -> None:
    preview = _load_json(PREVIEW_PATH)
    candidate = next(
        item
        for item in preview["candidates"]
        if item["item"]["id"] == "faq.mattermost.channel.creation.channel_limit"
    )
    content = candidate["item"]["content"]
    assert "清理" not in content
    assert "归档" not in content
    assert "删除" not in content
    assert "设置入口" not in content
    assert candidate["plan"]["missing_evidence"]
    assert candidate["review"]["missing_evidence"]


def test_creation_failure_is_a_gap_without_failure_or_rollback_evidence() -> None:
    case = next(case for case in _load_json(QA_PATH)["cases"] if case["id"] == "creation_creator_failure")
    assert case["expected_gap"] is True
    assert "创建失败一定不会留下成员关系" in case["forbidden_claims"]


def test_discoverable_candidate_describes_necessary_checks_without_promising_success() -> None:
    preview = _load_json(PREVIEW_PATH)
    candidate = next(
        item
        for item in preview["candidates"]
        if item["item"]["id"]
        == "faq.mattermost.channel.creation.discoverable_private_creation"
    )
    content = candidate["item"]["content"]
    assert "必要" in content
    assert "不代表" in content
    assert "才允许创建" not in content
    assert "这些条件都满足后" not in content
    assert candidate["plan"]["missing_evidence"]
    assert candidate["review"]["missing_evidence"]
