"""Read-only evaluation of generated L4 candidates.

The evaluator creates a short-lived in-memory catalog.  Accepted draft
candidates are represented as published only in that catalog so that the
normal USER serve path can be exercised without writing canonical Markdown or
changing a candidate's source status.  The resulting report is evidence for a
review, not a publish decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge import KnowledgeCatalog
from app.knowledge.l4_compiler import L4Candidate, L4Preview, validate_l4_plan
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.qa import QAResponder, answer_question
from app.knowledge.retrieval import retrieve


EVALUATION_TOP_K = 4


class L4EvaluationCase(BaseModel):
    """One mechanical regression case plus a human semantic rubric."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_knowledge_id: str | None = None
    expected_gap: bool = False
    required_claims: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)


class L4EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: str = Field(min_length=1)
    feature: str = Field(min_length=1)
    cases: list[L4EvaluationCase] = Field(min_length=1)


def _action(candidate: L4Candidate) -> str:
    raw = candidate.plan.action
    return str(getattr(raw, "value", raw))


def _candidate_errors(
    candidate: L4Candidate,
    *,
    catalog: KnowledgeCatalog,
    module: str,
    feature: str,
) -> list[str]:
    """Return only the acceptance checks that are part of this tool's contract."""

    errors: list[str] = []
    if len(set(candidate.intent.question_variants)) != len(candidate.intent.question_variants):
        errors.append("duplicate_question_variants")
    if any(not value.strip() for value in candidate.intent.question_variants):
        errors.append("blank_question_variant")
    if len(set(candidate.intent.candidate_rule_ids)) != len(candidate.intent.candidate_rule_ids):
        errors.append("duplicate_candidate_rule_ids")
    if len(set(candidate.intent.existing_knowledge_ids)) != len(candidate.intent.existing_knowledge_ids):
        errors.append("duplicate_existing_knowledge_ids")
    for existing_id in candidate.intent.existing_knowledge_ids:
        try:
            existing = catalog.get(existing_id)
        except KeyError:
            errors.append(f"existing_knowledge_missing:{existing_id}")
            continue
        if (
            existing.layer != KnowledgeLayer.L4_USER_KNOWLEDGE
            or existing.module != module
            or existing.feature != feature
        ):
            errors.append(f"existing_knowledge_out_of_scope:{existing_id}")
    for merge_id in candidate.plan.merge_ids:
        if merge_id not in catalog._items:
            errors.append(f"merge_target_missing:{merge_id}")
    try:
        validate_l4_plan(brief=candidate.intent, plan=candidate.plan, catalog=catalog)
    except ValueError as exc:
        errors.append(f"invalid_plan:{exc}")

    if _action(candidate) == "gap":
        # A gap is deliberately retained as a gap.  It has no draft asset to
        # promote and must never remove or replace an existing FAQ.
        return errors

    if candidate.item is None:
        errors.append("item_missing")
    if candidate.review is None:
        errors.append("review_missing")
    elif candidate.review.issues:
        errors.append("review_has_issues")
    if candidate.item is not None:
        if candidate.item.status != KnowledgeStatus.DRAFT:
            errors.append("item_not_draft")
        if candidate.item.layer != KnowledgeLayer.L4_USER_KNOWLEDGE:
            errors.append("item_not_l4")
        if candidate.item.id != candidate.intent.id:
            errors.append("item_id_mismatch")
        if candidate.item.title != candidate.intent.question:
            errors.append("item_title_mismatch")
        if candidate.item.question_variants != candidate.intent.question_variants:
            errors.append("question_variants_mismatch")
        if candidate.item.behavior_rule_ids != candidate.plan.rule_ids:
            errors.append("behavior_rule_ids_mismatch")
        if candidate.item.module != module:
            errors.append("item_module_out_of_scope")
        if candidate.item.feature != feature:
            errors.append("item_feature_out_of_scope")
        if UserRole.USER not in candidate.item.visible_roles:
            errors.append("item_not_user_visible")
    return errors


def _simulate_candidates(
    catalog: KnowledgeCatalog,
    preview: L4Preview,
) -> tuple[KnowledgeCatalog, dict[str, Any], set[str]]:
    """Build an in-memory serve catalog and candidate audit details.

    The returned set contains IDs replaced by accepted merge candidates.  It is
    used only for leakage reporting; it is not a retrieval filter.
    """

    items = dict(catalog._items)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    replaced_ids: set[str] = set()
    target_ids = {candidate.intent.id for candidate in preview.candidates}
    seen_candidate_ids: set[str] = set()
    seen_merge_ids: set[str] = set()

    for candidate in preview.candidates:
        action = _action(candidate)
        candidate_id = candidate.intent.id
        duplicate_errors: list[str] = []
        if candidate_id in seen_candidate_ids:
            duplicate_errors.append("duplicate_candidate_id")
        seen_candidate_ids.add(candidate_id)
        merge_ids = list(candidate.plan.merge_ids)
        if seen_merge_ids.intersection(merge_ids):
            duplicate_errors.append("overlapping_merge_targets")
        if set(merge_ids).intersection(target_ids - {candidate_id}):
            duplicate_errors.append("merge_target_is_another_candidate")
        seen_merge_ids.update(merge_ids)
        if action == "gap":
            if duplicate_errors:
                rejected.append({"id": candidate_id, "action": action, "errors": duplicate_errors})
                continue
            errors = _candidate_errors(
                candidate,
                catalog=catalog,
                module=preview.module,
                feature=preview.feature,
            )
            if errors:
                rejected.append({"id": candidate_id, "action": action, "errors": errors})
                continue
            gap = {
                "id": candidate_id,
                "action": action,
                "accepted": True,
                "missing_evidence": list(candidate.plan.missing_evidence),
                "item_id": candidate.item.id if candidate.item is not None else None,
            }
            gaps.append(gap)
            accepted.append({**gap, "simulation_status": "gap"})
            continue

        errors = duplicate_errors + _candidate_errors(
            candidate,
            catalog=catalog,
            module=preview.module,
            feature=preview.feature,
        )
        if errors:
            rejected.append({"id": candidate_id, "action": action, "errors": errors})
            continue

        # _candidate_errors guarantees this branch, but keeping the guard here
        # makes the mutation boundary obvious to future callers.
        if candidate.item is None:
            rejected.append({"id": candidate_id, "action": action, "errors": ["item_missing"]})
            continue

        # The candidate remains draft in the preview and on disk.  Only this
        # copied object is promoted for the simulated normal serve check.
        simulated_item = candidate.item.model_copy(update={"status": KnowledgeStatus.PUBLISHED})
        retired_ids = [old_id for old_id in merge_ids if old_id != simulated_item.id]
        for old_id in merge_ids:
            if old_id in items:
                items.pop(old_id)
            # A stable ID can be listed in merge_ids while its old content is
            # being replaced.  It is retained by the candidate and therefore
            # is not an old-ID leakage.  Aliases really are retired IDs.
            if old_id != simulated_item.id:
                replaced_ids.add(old_id)
        items[simulated_item.id] = simulated_item
        accepted.append(
            {
                "id": candidate_id,
                "action": action,
                "accepted": True,
                "item_id": simulated_item.id,
                "source_status": candidate.item.status.value,
                "simulation_status": simulated_item.status.value,
                "merge_ids": merge_ids,
                "replaced_ids": retired_ids,
            }
        )

    details = {
        "total": len(preview.candidates),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "gap_count": len(gaps),
        "accepted_candidates": accepted,
        "rejected_candidates": rejected,
        "gap_candidates": gaps,
    }
    return KnowledgeCatalog(list(items.values())), details, replaced_ids


def build_candidate_catalog(catalog: KnowledgeCatalog, preview: L4Preview) -> KnowledgeCatalog:
    """Return a simulated catalog without changing the supplied catalog.

    Only candidates with a draft L4 item, a review, and no review issues are
    promoted in memory.  Gap candidates are intentionally left out of the
    catalog and never replace an existing item.
    """

    simulated, _details, _replaced_ids = _simulate_candidates(catalog, preview)
    return simulated


def _coerce_cases(cases: Sequence[L4EvaluationCase | Mapping[str, Any]]) -> list[L4EvaluationCase]:
    result: list[L4EvaluationCase] = []
    for case in cases:
        if isinstance(case, L4EvaluationCase):
            result.append(case)
        else:
            result.append(L4EvaluationCase.model_validate(case))
    return result


def validate_evaluation_cases(
    preview: L4Preview,
    cases: Sequence[L4EvaluationCase | Mapping[str, Any]],
) -> list[L4EvaluationCase]:
    """Validate case identity and target scope before any optional QA call."""

    evaluation_cases = _coerce_cases(cases)
    if not evaluation_cases:
        raise ValueError("evaluation cases must not be empty")
    case_ids = [case.id for case in evaluation_cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("duplicate case id")

    preview_target_ids = {candidate.intent.id for candidate in preview.candidates}
    for case in evaluation_cases:
        if case.expected_knowledge_id is None:
            if not case.expected_gap:
                raise ValueError(
                    f"case {case.id} must declare expected_knowledge_id unless expected_gap=true"
                )
            continue
        if case.expected_knowledge_id not in preview_target_ids:
            raise ValueError(
                f"case {case.id} expected target is not a preview target: "
                f"{case.expected_knowledge_id}"
            )
    return evaluation_cases


def _old_ids_in_order(retrieved: list[str], replaced_ids: set[str]) -> list[str]:
    return list(dict.fromkeys(knowledge_id for knowledge_id in retrieved if knowledge_id in replaced_ids))


def _mechanical_qa_pass(
    case: L4EvaluationCase,
    *,
    cites: list[str],
    gap: bool,
    old_ids_leaked: list[str],
) -> bool:
    """Check only citation/gap mechanics; semantic claims stay human-reviewed."""

    if case.expected_gap:
        return gap and not cites
    if case.expected_knowledge_id is None:
        return False
    return (
        not gap
        and case.expected_knowledge_id in cites
        and not old_ids_leaked
    )


async def evaluate_l4_preview(
    catalog: KnowledgeCatalog,
    preview: L4Preview,
    cases: Sequence[L4EvaluationCase | Mapping[str, Any]],
    responder: QAResponder | None = None,
) -> dict[str, Any]:
    """Evaluate a preview through the ordinary USER/local serve path.

    Retrieval always uses ``UserRole.USER`` and ``review_mode=False``.  If a
    responder is supplied, the same restrictions are passed to
    :func:`answer_question`; the caller may use a fake responder for offline
    tests.  No canonical files, statuses, vector index, or database are
    touched.
    """

    evaluation_cases = validate_evaluation_cases(preview, cases)
    simulated, candidate_details, replaced_ids = _simulate_candidates(catalog, preview)
    records: list[dict[str, Any]] = []

    for case in evaluation_cases:
        hits = retrieve(
            simulated,
            case.question,
            UserRole.USER,
            top_k=EVALUATION_TOP_K,
            review_mode=False,
        )
        retrieved = [hit.item.id for hit in hits]
        target_rank = None
        if case.expected_knowledge_id is not None and case.expected_knowledge_id in retrieved:
            target_rank = retrieved.index(case.expected_knowledge_id) + 1
        target_hit = target_rank is not None
        old_ids_leaked = _old_ids_in_order(retrieved, replaced_ids)
        retrieval_evaluable = case.expected_knowledge_id is not None
        retrieval_pass = (
            target_hit and not old_ids_leaked and case.expected_knowledge_id is not None
            if retrieval_evaluable
            else None
        )

        record: dict[str, Any] = {
            "id": case.id,
            "question": case.question,
            "retrieved": retrieved,
            "expected_knowledge_id": case.expected_knowledge_id,
            "expected_gap": case.expected_gap,
            "target_rank": target_rank,
            "target_hit": target_hit,
            "old_ids_leaked": old_ids_leaked,
            "old_id_leaked": bool(old_ids_leaked),
            "retrieval_evaluable": retrieval_evaluable,
            "retrieval_pass": retrieval_pass,
            "required_claims": list(case.required_claims),
            "forbidden_claims": list(case.forbidden_claims),
            "rubric": {
                "required_claims": list(case.required_claims),
                "forbidden_claims": list(case.forbidden_claims),
            },
            # An absent rubric is not evidence that semantic review has passed.
            "semantic_review_pending": True,
            "qa_evaluable": responder is not None,
            "needs_qa": responder is None,
        }

        if responder is not None:
            result = await answer_question(
                catalog=simulated,
                question=case.question,
                role=UserRole.USER,
                responder=responder,
                top_k=EVALUATION_TOP_K,
                backend="local",
                vector_index=None,
                embedder=None,
                reranker=None,
                intent_classifier=None,
                review_mode=False,
            )
            cites = [str(value) for value in result.get("cites", [])]
            answer = str(result.get("answer", ""))
            gap = bool(result.get("knowledge_gap", False))
            qa_old_ids = _old_ids_in_order(list(dict.fromkeys([*retrieved, *cites])), replaced_ids)
            old_ids_leaked = list(dict.fromkeys([*old_ids_leaked, *qa_old_ids]))
            record.update(
                {
                    "answer": answer,
                    "cites": cites,
                    "gap": gap,
                    "qa_pass": _mechanical_qa_pass(
                        case,
                        cites=cites,
                        gap=gap,
                        old_ids_leaked=old_ids_leaked,
                    ),
                    "needs_qa": False,
                }
            )

        records.append(record)

    retrieval_records = [record for record in records if record["retrieval_evaluable"]]
    qa_records = [record for record in records if record["qa_evaluable"]]
    return {
        "simulation": True,
        "published": False,
        "mode": "simulation",
        "module": preview.module,
        "feature": preview.feature,
        "candidates": candidate_details,
        "cases": records,
        "retrieval_backend": "local",
        "retrieval_role": UserRole.USER.value,
        "review_mode": False,
        "top_k": EVALUATION_TOP_K,
        "retrieval_passed": sum(bool(record["retrieval_pass"]) for record in retrieval_records),
        "retrieval_total": len(retrieval_records),
        "qa_passed": sum(bool(record.get("qa_pass")) for record in qa_records),
        "qa_total": len(qa_records),
        "semantic_review_pending": sum(
            bool(record["semantic_review_pending"]) for record in records
        ),
        "proof_boundary": [
            "simulation only; canonical knowledge files were not written",
            "candidate source status stayed draft; only the in-memory copy was treated as published",
            "retrieval used UserRole.USER with review_mode=False and local BM25",
            "citation and gap checks are mechanical; required/forbidden claims need human semantic review",
            "this report is not an HTTP end-to-end or production publish verification",
        ],
    }
