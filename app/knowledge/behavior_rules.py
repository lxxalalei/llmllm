from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.knowledge.keys import normalize_knowledge_key
from app.knowledge.models import KnowledgeItem, KnowledgeLayer


RuleScalar = str | int | float | bool
RuleValue = RuleScalar | list[RuleScalar] | None


class RulePredicate(BaseModel):
    """One explicit condition copied from or directly supported by source evidence."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: RuleValue = None


class RuleConditions(BaseModel):
    """Small condition tree: all predicates must match and one `any` predicate may match."""

    model_config = ConfigDict(extra="forbid")

    all: list[RulePredicate] = Field(default_factory=list)
    any: list[RulePredicate] = Field(default_factory=list)


class RuleEffect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1)
    target: str = Field(min_length=1)
    detail: str | None = None


class RuleException(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conditions: RuleConditions
    outcome: str = Field(min_length=1)


class BehaviorRuleDraft(BaseModel):
    """Model-produced candidate before source-fact IDs are validated."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    conditions: RuleConditions = Field(default_factory=RuleConditions)
    decision: str | None = None
    state_changes: list[RuleEffect] = Field(default_factory=list)
    side_effects: list[RuleEffect] = Field(default_factory=list)
    exceptions: list[RuleException] = Field(default_factory=list)
    source_fact_ids: list[str] = Field(min_length=1)

    _normalize_key = field_validator("key", mode="before")(normalize_knowledge_key)


class BehaviorRuleBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[BehaviorRuleDraft] = Field(default_factory=list)


class BehaviorRule(BaseModel):
    """Canonical structured behavior shared by engineering/product/user views."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^rule\.[a-z0-9_.]+$")
    title: str
    domain: str
    capability: str
    actor: str
    action: str
    resource: str
    conditions: RuleConditions = Field(default_factory=RuleConditions)
    decision: str | None = None
    state_changes: list[RuleEffect] = Field(default_factory=list)
    side_effects: list[RuleEffect] = Field(default_factory=list)
    exceptions: list[RuleException] = Field(default_factory=list)
    source_fact_ids: list[str] = Field(min_length=1)


class BehaviorRuleExtractor(Protocol):
    async def extract(self, facts: list[KnowledgeItem]) -> BehaviorRuleBatch: ...


class BehaviorRuleGenerator:
    """Turn L1 facts into structured rules without letting the model invent evidence IDs."""

    def __init__(self, extractor: BehaviorRuleExtractor) -> None:
        self._extractor = extractor

    async def generate(
        self, *, namespace: str, facts: list[KnowledgeItem]
    ) -> list[BehaviorRule]:
        invalid_layers = [item.id for item in facts if item.layer != KnowledgeLayer.L1_ENGINEERING_FACT]
        if invalid_layers:
            raise ValueError(
                "behavior rules require L1 engineering facts: " + ", ".join(sorted(invalid_layers))
            )

        batch = await self._extractor.extract(facts)
        allowed = {item.id for item in facts}
        result: list[BehaviorRule] = []
        seen: set[str] = set()

        for draft in batch.rules:
            unknown = set(draft.source_fact_ids) - allowed
            if unknown:
                raise ValueError(
                    "behavior rule references unknown L1 facts: " + ", ".join(sorted(unknown))
                )

            rule_id = f"rule.{namespace}.{draft.key}"
            if rule_id in seen:
                raise ValueError(f"duplicate behavior rule id: {rule_id}")
            seen.add(rule_id)

            result.append(
                BehaviorRule(
                    id=rule_id,
                    title=draft.title.strip(),
                    domain=draft.domain.strip(),
                    capability=draft.capability.strip(),
                    actor=draft.actor.strip(),
                    action=draft.action.strip(),
                    resource=draft.resource.strip(),
                    conditions=draft.conditions,
                    decision=draft.decision.strip() if draft.decision else None,
                    state_changes=draft.state_changes,
                    side_effects=draft.side_effects,
                    exceptions=draft.exceptions,
                    source_fact_ids=list(dict.fromkeys(draft.source_fact_ids)),
                )
            )

        return result

    async def close(self) -> None:
        close = getattr(self._extractor, "close", None)
        if close is not None:
            await close()
