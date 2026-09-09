"""Compile user-intent drafts from bounded, canonical BehaviorRule evidence."""
from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge.assets import KnowledgeCatalog
from app.knowledge.behavior_rules import BehaviorRule
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class L4IntentBrief(_Contract):
    id: str = Field(pattern=r"^faq\.[a-z0-9_.]+$")
    question: str = Field(min_length=1)
    question_variants: list[str]
    candidate_rule_ids: list[str]
    existing_knowledge_ids: list[str]


class L4IntentManifest(_Contract):
    module: str = Field(min_length=1)
    feature: str = Field(min_length=1)
    intents: list[L4IntentBrief] = Field(min_length=1)


class L4Plan(_Contract):
    action: Literal["create", "merge", "gap"]
    rule_ids: list[str]
    merge_ids: list[str]
    rationale: str = Field(min_length=1)
    missing_evidence: list[str]


class L4Draft(_Contract):
    answer: str = Field(min_length=1)


class L4Review(_Contract):
    issues: list[str]
    missing_evidence: list[str]


class L4Candidate(_Contract):
    intent: L4IntentBrief
    plan: L4Plan
    item: KnowledgeItem | None
    review: L4Review | None


class L4Preview(_Contract):
    module: str
    feature: str
    candidates: list[L4Candidate]


class L4Composer(Protocol):
    async def plan(self, *, brief: L4IntentBrief, rules: list[BehaviorRule], existing_items: list[KnowledgeItem]) -> L4Plan: ...
    async def write(self, *, brief: L4IntentBrief, plan: L4Plan, rules: list[BehaviorRule]) -> L4Draft: ...
    async def review(self, *, brief: L4IntentBrief, draft: L4Draft, rules: list[BehaviorRule]) -> L4Review: ...


def _unique(values: list[str], label: str) -> None:
    if any(not value.strip() for value in values) or len(set(values)) != len(values):
        raise ValueError(f"blank or duplicate {label}")


def _get(catalog: KnowledgeCatalog, knowledge_id: str) -> KnowledgeItem:
    try:
        return catalog.get(knowledge_id)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc


def validate_l4_inputs(*, manifest: L4IntentManifest, catalog: KnowledgeCatalog, rules: list[BehaviorRule]) -> dict[str, list[str]]:
    """Preflight the entire batch before spending any model calls."""
    _unique([rule.id for rule in rules], "rule IDs")
    _unique([brief.id for brief in manifest.intents], "intent IDs")
    rule_map = {rule.id: rule for rule in rules}
    view_ids: dict[str, list[str]] = {}
    eligible = {KnowledgeStatus.REVIEW, KnowledgeStatus.PUBLISHED}

    def in_scope(item: KnowledgeItem, layer: KnowledgeLayer) -> bool:
        return item.layer == layer and item.module == manifest.module and item.feature == manifest.feature

    for brief in manifest.intents:
        _unique(brief.question_variants, "question variants")
        _unique(brief.candidate_rule_ids, "candidate rule IDs")
        _unique(brief.existing_knowledge_ids, "existing knowledge IDs")
        if brief.id in catalog._items and brief.id not in brief.existing_knowledge_ids:
            raise ValueError(f"existing target must be declared: {brief.id}")
        for knowledge_id in brief.existing_knowledge_ids:
            if not in_scope(_get(catalog, knowledge_id), KnowledgeLayer.L4_USER_KNOWLEDGE):
                raise ValueError(f"existing knowledge outside L4 scope: {knowledge_id}")
        for rule_id in brief.candidate_rule_ids:
            rule = rule_map.get(rule_id)
            if rule is None or rule.domain != manifest.module:
                raise ValueError(f"unknown or out-of-scope rule: {rule_id}")
            for fact_id in rule.source_fact_ids:
                fact = _get(catalog, fact_id)
                if not in_scope(fact, KnowledgeLayer.L1_ENGINEERING_FACT) or fact.status not in eligible or not fact.sources:
                    raise ValueError(f"rule requires reviewed L1 source evidence: {fact_id}")
            views = [item for item in catalog._items.values() if in_scope(item, KnowledgeLayer.L3_PRODUCT_LOGIC) and item.status in eligible and rule_id in item.linked_behavior_rule_ids]
            grounded = []
            for view in views:
                try:
                    lineage = catalog.trace_lineage(view.id)
                except KeyError as exc:
                    raise ValueError(f"broken L3 lineage: {view.id}") from exc
                if set(rule.source_fact_ids) <= {item.id for item in lineage}:
                    grounded.append(view.id)
            if not grounded:
                raise ValueError(f"rule requires a grounded reviewed L3 view: {rule_id}")
            view_ids[rule_id] = sorted(grounded)
    return view_ids


def validate_l4_plan(*, brief: L4IntentBrief, plan: L4Plan, catalog: KnowledgeCatalog) -> None:
    _unique(plan.rule_ids, "plan rule IDs")
    _unique(plan.merge_ids, "plan merge IDs")
    if not set(plan.rule_ids) <= set(brief.candidate_rule_ids):
        raise ValueError("plan references a rule outside the intent evidence")
    if not set(plan.merge_ids) <= set(brief.existing_knowledge_ids):
        raise ValueError("plan merge references undeclared knowledge")
    if plan.action == "gap":
        if not any(value.strip() for value in plan.missing_evidence) or plan.merge_ids:
            raise ValueError("gap requires missing evidence and no merge")
        return
    if not plan.rule_ids:
        raise ValueError("create/merge requires rule evidence")
    if plan.action == "create" and (plan.merge_ids or brief.id in catalog._items):
        raise ValueError("create cannot merge or overwrite existing knowledge")
    if plan.action == "merge" and not plan.merge_ids:
        raise ValueError("merge requires existing knowledge IDs")
    if brief.id in catalog._items and brief.id not in plan.merge_ids:
        raise ValueError("merge must explicitly include its existing target")


async def compile_l4_preview(*, manifest: L4IntentManifest, catalog: KnowledgeCatalog, rules: list[BehaviorRule], composer: L4Composer) -> L4Preview:
    view_ids = validate_l4_inputs(manifest=manifest, catalog=catalog, rules=rules)
    rule_map = {rule.id: rule for rule in rules}
    planned: list[tuple[L4IntentBrief, L4Plan]] = []
    replaced: set[str] = set()
    targets = {brief.id for brief in manifest.intents}
    # Plan the full batch before writing so overlapping replacement proposals fail early.
    for brief in manifest.intents:
        plan = await composer.plan(brief=brief, rules=[rule_map[rid] for rid in brief.candidate_rule_ids], existing_items=[catalog.get(kid) for kid in brief.existing_knowledge_ids])
        validate_l4_plan(brief=brief, plan=plan, catalog=catalog)
        if replaced.intersection(plan.merge_ids) or (set(plan.merge_ids) & (targets - {brief.id})):
            raise ValueError("overlapping merge proposals across intents")
        replaced.update(plan.merge_ids)
        planned.append((brief, plan))

    candidates = []
    for brief, plan in planned:
        if plan.action == "gap":
            candidates.append(L4Candidate(intent=brief, plan=plan, item=None, review=None))
            continue
        selected = [rule_map[rid] for rid in plan.rule_ids]
        draft = await composer.write(brief=brief, plan=plan, rules=selected)
        review = await composer.review(brief=brief, draft=draft, rules=selected)
        item = KnowledgeItem(
            id=brief.id, title=brief.question, question_variants=brief.question_variants,
            layer=KnowledgeLayer.L4_USER_KNOWLEDGE, module=manifest.module, feature=manifest.feature,
            content=draft.answer, status=KnowledgeStatus.DRAFT,
            behavior_rule_ids=plan.rule_ids,
            derived_from=list(dict.fromkeys(vid for rid in plan.rule_ids for vid in view_ids[rid])),
            visible_roles=list(UserRole),
        )
        candidates.append(L4Candidate(intent=brief, plan=plan, item=item, review=review))
    return L4Preview(module=manifest.module, feature=manifest.feature, candidates=candidates)
