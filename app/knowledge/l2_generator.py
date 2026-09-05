from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole


class EngineeringRuleDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str
    statement: str
    derived_from: list[str] = Field(min_length=1)


class EngineeringRuleBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[EngineeringRuleDraft]


class EngineeringRuleExtractor(Protocol):
    async def extract(
        self,
        facts: list[KnowledgeItem],
        existing_rules: list[KnowledgeItem],
    ) -> EngineeringRuleBatch: ...


class L2Generator:
    """Synthesize developer-facing engineering rules from the current L1 scope."""

    def __init__(self, extractor: EngineeringRuleExtractor) -> None:
        self._extractor = extractor

    async def generate(
        self,
        *,
        namespace: str,
        module: str,
        feature: str,
        l1_items: list[KnowledgeItem],
        existing_items: list[KnowledgeItem],
    ) -> list[KnowledgeItem]:
        if not l1_items:
            return []

        batch = await self._extractor.extract(l1_items, existing_items)
        allowed_l1 = {item.id for item in l1_items}
        items: list[KnowledgeItem] = []
        seen_ids: set[str] = set()

        for rule in batch.rules:
            unknown = set(rule.derived_from) - allowed_l1
            if unknown:
                raise ValueError(
                    "model returned unknown L1 dependency: " + ", ".join(sorted(unknown))
                )

            knowledge_id = f"eng.{namespace}.{rule.key}"
            if knowledge_id in seen_ids:
                raise ValueError(f"model returned duplicate knowledge id: {knowledge_id}")
            seen_ids.add(knowledge_id)

            items.append(
                KnowledgeItem(
                    id=knowledge_id,
                    title=rule.title.strip(),
                    layer=KnowledgeLayer.L2_ENGINEERING_RULE,
                    module=module,
                    feature=feature,
                    content=rule.statement.strip(),
                    status=KnowledgeStatus.DRAFT,
                    derived_from=list(dict.fromkeys(rule.derived_from)),
                    visible_roles=[UserRole.DEVELOPER, UserRole.TEST, UserRole.PRODUCT],
                )
            )
        return items

    async def close(self) -> None:
        close = getattr(self._extractor, "close", None)
        if close is not None:
            await close()
