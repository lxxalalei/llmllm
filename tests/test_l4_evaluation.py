from __future__ import annotations

import pytest

from app.knowledge import KnowledgeCatalog
from app.knowledge.l4_compiler import (
    L4Candidate,
    L4IntentBrief,
    L4Plan,
    L4Preview,
    L4Review,
)
from app.knowledge.l4_evaluation import (
    EVALUATION_TOP_K,
    build_candidate_catalog,
    evaluate_l4_preview,
    validate_evaluation_cases,
)
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from scripts.evaluate_l4 import _report_has_failure
from scripts.evaluate_l4 import validate_output_path


MODULE = "demo.product"
FEATURE = "new_question"
OLD_ID = "faq.demo.old"
NEW_ID = "faq.demo.new"


def _item(
    knowledge_id: str,
    *,
    status: KnowledgeStatus = KnowledgeStatus.PUBLISHED,
    content: str = "The old answer.",
) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title=knowledge_id,
        layer=KnowledgeLayer.L4_USER_KNOWLEDGE,
        module=MODULE,
        feature=FEATURE,
        content=content,
        status=status,
        visible_roles=[UserRole.USER],
        question_variants=[content],
    )


def _candidate(
    *,
    candidate_id: str,
    action: str,
    item: KnowledgeItem | None,
    review: L4Review | None,
    merge_ids: list[str] | None = None,
    existing_ids: list[str] | None = None,
    rule_ids: list[str] | None = None,
    missing_evidence: list[str] | None = None,
) -> L4Candidate:
    selected_rules = rule_ids if rule_ids is not None else (["rule.demo"] if action != "gap" else [])
    intent = L4IntentBrief(
        id=candidate_id,
        question=item.title if item is not None else "What is the new answer?",
        question_variants=item.question_variants if item is not None else ["new answer"],
        candidate_rule_ids=selected_rules,
        existing_knowledge_ids=existing_ids or [],
    )
    plan = L4Plan(
        action=action,
        rule_ids=selected_rules,
        merge_ids=merge_ids or [],
        rationale="candidate evaluation",
        missing_evidence=missing_evidence if missing_evidence is not None else (["no evidence"] if action == "gap" else []),
    )
    if item is not None:
        item = item.model_copy(update={"behavior_rule_ids": selected_rules})
    return L4Candidate(intent=intent, plan=plan, item=item, review=review)


def _preview(candidates: list[L4Candidate]) -> L4Preview:
    return L4Preview(module=MODULE, feature=FEATURE, candidates=candidates)


def test_build_candidate_catalog_simulates_publish_and_replaces_merge_ids() -> None:
    original = KnowledgeCatalog([_item(OLD_ID, content="old answer about quux")])
    draft = _item(
        NEW_ID,
        status=KnowledgeStatus.DRAFT,
        content="new answer about quux and the candidate rule",
    )
    accepted = _candidate(
        candidate_id=NEW_ID,
        action="merge",
        item=draft,
        review=L4Review(issues=[], missing_evidence=[]),
        merge_ids=[OLD_ID],
        existing_ids=[OLD_ID],
    )
    rejected_published = _candidate(
        candidate_id="faq.demo.published",
        action="create",
        item=_item("faq.demo.published", content="must not be accepted"),
        review=L4Review(issues=[], missing_evidence=[]),
    )
    rejected_review = _candidate(
        candidate_id="faq.demo.reviewed",
        action="create",
        item=_item(
            "faq.demo.reviewed",
            status=KnowledgeStatus.DRAFT,
            content="must not be accepted because review has issues",
        ),
        review=L4Review(issues=["missing authorization evidence"], missing_evidence=[]),
    )
    gap = _candidate(
        candidate_id="faq.demo.gap",
        action="gap",
        item=None,
        review=None,
    )

    simulated = build_candidate_catalog(
        original,
        _preview([accepted, rejected_published, rejected_review, gap]),
    )

    assert OLD_ID not in simulated._items
    assert simulated.get(NEW_ID).status == KnowledgeStatus.PUBLISHED
    assert simulated.get(NEW_ID).content == draft.content
    assert "faq.demo.published" not in simulated._items
    assert "faq.demo.reviewed" not in simulated._items
    assert original.get(OLD_ID).status == KnowledgeStatus.PUBLISHED
    assert draft.status == KnowledgeStatus.DRAFT


@pytest.mark.asyncio
async def test_evaluation_uses_user_serve_mode_and_keeps_gap_as_pending_qa() -> None:
    original = KnowledgeCatalog([_item(OLD_ID, content="old answer about quux")])
    draft = _item(
        NEW_ID,
        status=KnowledgeStatus.DRAFT,
        content="new answer about quux and the candidate rule",
    )
    preview = _preview(
        [
            _candidate(
                candidate_id=NEW_ID,
                action="merge",
                item=draft,
                review=L4Review(issues=[], missing_evidence=[]),
                merge_ids=[OLD_ID],
                existing_ids=[OLD_ID],
            ),
            _candidate(
                candidate_id="faq.demo.gap",
                action="gap",
                item=None,
                review=None,
            ),
        ]
    )
    cases = [
        {
            "id": "covered",
            "question": "What is the candidate rule for quux?",
            "expected_knowledge_id": NEW_ID,
            "expected_gap": False,
            "required_claims": ["explain the candidate rule"],
            "forbidden_claims": ["invent an old rule"],
        },
        {
            "id": "unknown",
            "question": "What is the zorbaflux retention policy?",
            "expected_knowledge_id": None,
            "expected_gap": True,
            "required_claims": [],
            "forbidden_claims": [],
        },
    ]

    report = await evaluate_l4_preview(original, preview, cases)

    assert report["simulation"] is True
    assert report["published"] is False
    assert report["proof_boundary"][0] == "simulation only; canonical knowledge files were not written"
    covered = next(case for case in report["cases"] if case["id"] == "covered")
    assert covered["retrieved"][0] == NEW_ID
    assert covered["target_rank"] == 1
    assert covered["target_hit"] is True
    assert covered["old_ids_leaked"] == []
    assert covered["retrieval_pass"] is True
    assert covered["semantic_review_pending"] is True
    unknown = next(case for case in report["cases"] if case["id"] == "unknown")
    assert unknown["retrieval_evaluable"] is False
    assert unknown["needs_qa"] is True
    assert unknown["semantic_review_pending"] is True
    assert report["retrieval_passed"] == 1
    assert report["retrieval_total"] == 1
    assert report["qa_total"] == 0
    assert original.get(OLD_ID).status == KnowledgeStatus.PUBLISHED
    assert draft.status == KnowledgeStatus.DRAFT


@pytest.mark.asyncio
async def test_evaluation_uses_production_top_k_and_gap_target_still_requires_a_hit() -> None:
    original = KnowledgeCatalog([_item(OLD_ID, content="old answer about quux")])
    draft = _item(
        NEW_ID,
        status=KnowledgeStatus.DRAFT,
        content="new answer about quux and the candidate rule",
    )
    preview = _preview(
        [
            _candidate(
                candidate_id=NEW_ID,
                action="merge",
                item=draft,
                review=L4Review(issues=[], missing_evidence=[]),
                merge_ids=[OLD_ID],
                existing_ids=[OLD_ID],
            )
        ]
    )
    report = await evaluate_l4_preview(
        original,
        preview,
        [
            {
                "id": "gap_with_related_faq",
                "question": "What is the candidate rule for quux?",
                "expected_knowledge_id": NEW_ID,
                "expected_gap": True,
                "required_claims": [],
                "forbidden_claims": [],
            }
        ],
    )

    case = report["cases"][0]
    assert EVALUATION_TOP_K == 4
    assert report["top_k"] == 4
    assert case["target_hit"] is True
    assert case["retrieval_pass"] is True
    assert case["retrieval_evaluable"] is True
    assert case["needs_qa"] is True


@pytest.mark.asyncio
async def test_same_id_merge_does_not_report_the_retained_id_as_old_leakage() -> None:
    original = KnowledgeCatalog(
        [
            _item(NEW_ID, content="old answer for the same stable id"),
            _item(OLD_ID, content="old alias answer about quux"),
        ]
    )
    draft = _item(
        NEW_ID,
        status=KnowledgeStatus.DRAFT,
        content="new answer about quux and the candidate rule",
    )
    preview = _preview(
        [
            _candidate(
                candidate_id=NEW_ID,
                action="merge",
                item=draft,
                review=L4Review(issues=[], missing_evidence=[]),
                merge_ids=[NEW_ID, OLD_ID],
                existing_ids=[NEW_ID, OLD_ID],
            )
        ]
    )

    simulated = build_candidate_catalog(original, preview)
    assert simulated.get(NEW_ID).content == draft.content
    assert OLD_ID not in simulated._items
    report = await evaluate_l4_preview(
        original,
        preview,
        [
            {
                "id": "same_id_merge",
                "question": "What is the candidate rule for quux?",
                "expected_knowledge_id": NEW_ID,
                "expected_gap": False,
                "required_claims": [],
                "forbidden_claims": [],
            }
        ],
    )
    assert report["cases"][0]["retrieved"] == [NEW_ID]
    assert report["cases"][0]["old_ids_leaked"] == []
    accepted = report["candidates"]["accepted_candidates"][0]
    assert accepted["merge_ids"] == [NEW_ID, OLD_ID]
    assert accepted["replaced_ids"] == [OLD_ID]


@pytest.mark.asyncio
async def test_rejected_candidates_are_reported_and_fail_cli_even_when_cases_pass() -> None:
    original = KnowledgeCatalog([_item(OLD_ID, content="old answer about quux")])
    invalid = _candidate(
        candidate_id=OLD_ID,
        action="create",
        item=_item(OLD_ID, content="must be rejected"),
        review=L4Review(issues=["review issue"], missing_evidence=[]),
    )
    report = await evaluate_l4_preview(
        original,
        _preview([invalid]),
        [
            {
                "id": "old_case",
                "question": "What is the old answer for quux?",
                "expected_knowledge_id": OLD_ID,
                "expected_gap": False,
                "required_claims": [],
                "forbidden_claims": [],
            }
        ],
    )

    assert report["candidates"]["rejected_count"] == 1
    assert _report_has_failure(report, with_llm=False) is True


class _FakeResponder:
    def __init__(self, expected_id: str) -> None:
        self.expected_id = expected_id
        self.calls: list[tuple[str, list[str], list[KnowledgeStatus], str]] = []

    async def answer(self, question, context, mode="grounded"):
        self.calls.append(
            (
                question,
                [hit.item.id for hit in context],
                [hit.item.status for hit in context],
                mode,
            )
        )
        if "zorbaflux" in question:
            return {"answer": "No published coverage yet.", "cites": [], "knowledge_gap": True}
        return {
            "answer": "The candidate rule applies to quux.",
            "cites": [self.expected_id],
            "knowledge_gap": False,
        }

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_fake_qa_checks_citations_and_gap_without_auto_passing_semantic_rubric() -> None:
    original = KnowledgeCatalog([_item(OLD_ID, content="old answer about quux")])
    draft = _item(
        NEW_ID,
        status=KnowledgeStatus.DRAFT,
        content="new answer about quux and the candidate rule",
    )
    preview = _preview(
        [
            _candidate(
                candidate_id=NEW_ID,
                action="merge",
                item=draft,
                review=L4Review(issues=[], missing_evidence=[]),
                merge_ids=[OLD_ID],
                existing_ids=[OLD_ID],
            )
        ]
    )
    responder = _FakeResponder(NEW_ID)
    report = await evaluate_l4_preview(
        original,
        preview,
        [
            {
                "id": "covered",
                "question": "What is the candidate rule for quux?",
                "expected_knowledge_id": NEW_ID,
                "expected_gap": False,
                "required_claims": ["this must be reviewed by a human"],
                "forbidden_claims": [],
            },
            {
                "id": "unknown",
                "question": "What is the zorbaflux retention policy?",
                "expected_knowledge_id": None,
                "expected_gap": True,
                "required_claims": [],
                "forbidden_claims": [],
            },
        ],
        responder=responder,
    )

    covered = next(case for case in report["cases"] if case["id"] == "covered")
    assert covered["answer"] == "The candidate rule applies to quux."
    assert covered["cites"] == [NEW_ID]
    assert covered["gap"] is False
    assert covered["qa_pass"] is True
    assert covered["semantic_review_pending"] is True
    unknown = next(case for case in report["cases"] if case["id"] == "unknown")
    assert unknown["answer"] == "No published coverage yet."
    assert unknown["cites"] == []
    assert unknown["gap"] is True
    assert unknown["needs_qa"] is False
    assert unknown["qa_pass"] is True
    assert all(status == KnowledgeStatus.PUBLISHED for _, _, statuses, _ in responder.calls for status in statuses)
    assert all(mode == "grounded" for _, _, _, mode in responder.calls)
    assert report["qa_passed"] == 2
    assert report["qa_total"] == 2


def test_dataset_cases_reject_duplicates_unknown_targets_and_extra_fields() -> None:
    preview = _preview(
        [
            _candidate(
                candidate_id=NEW_ID,
                action="create",
                item=_item(NEW_ID, status=KnowledgeStatus.DRAFT, content="new answer"),
                review=L4Review(issues=[], missing_evidence=[]),
            )
        ]
    )
    duplicate_cases = [
        {
            "id": "same",
            "question": "one",
            "expected_knowledge_id": NEW_ID,
            "expected_gap": False,
            "required_claims": [],
            "forbidden_claims": [],
        },
        {
            "id": "same",
            "question": "two",
            "expected_knowledge_id": NEW_ID,
            "expected_gap": False,
            "required_claims": [],
            "forbidden_claims": [],
        },
    ]
    with pytest.raises(ValueError, match="duplicate case id"):
        validate_evaluation_cases(preview, duplicate_cases)

    with pytest.raises(ValueError, match="not a preview target"):
        validate_evaluation_cases(
            preview,
            [
                {
                    "id": "unknown_target",
                    "question": "question",
                    "expected_knowledge_id": "faq.demo.not_in_preview",
                    "expected_gap": True,
                    "required_claims": [],
                    "forbidden_claims": [],
                }
            ],
        )

    with pytest.raises(ValueError, match="extra"):
        from app.knowledge.l4_evaluation import L4EvaluationDataset

        L4EvaluationDataset.model_validate(
            {
                "module": MODULE,
                "feature": FEATURE,
                "cases": [],
                "quesitons": [],
            }
        )


def test_cli_output_cannot_overwrite_inputs_or_canonical_root(tmp_path) -> None:
    knowledge_root = tmp_path / "knowledge"
    knowledge_root.mkdir()
    preview = tmp_path / "preview.json"
    dataset = tmp_path / "dataset.json"
    preview.write_text("{}", encoding="utf-8")
    dataset.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical knowledge root"):
        validate_output_path(knowledge_root / "report.json", [knowledge_root], [preview, dataset])
    with pytest.raises(ValueError, match="overwrite an input"):
        validate_output_path(preview, [knowledge_root], [preview, dataset])
    with pytest.raises(ValueError, match="must be JSON"):
        validate_output_path(tmp_path / "report.txt", [knowledge_root], [preview, dataset])
