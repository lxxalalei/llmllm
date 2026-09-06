from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.knowledge.keys import normalize_knowledge_key
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole


class ProductLogicDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str
    statement: str
    derived_from: list[str] = Field(min_length=1, max_length=1)

    _normalize_key = field_validator("key", mode="before")(normalize_knowledge_key)


class ProductLogicBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProductLogicDraft] = Field(min_length=1, max_length=15)


class UserKnowledgeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    question: str
    answer: str
    derived_from: list[str] = Field(min_length=1, max_length=1)

    _normalize_key = field_validator("key", mode="before")(normalize_knowledge_key)


class UserKnowledgeBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UserKnowledgeDraft] = Field(min_length=1, max_length=30)


class ProductLogicExtractor(Protocol):
    async def extract(self, rules: list[KnowledgeItem]) -> ProductLogicBatch: ...


class UserKnowledgeExtractor(Protocol):
    async def extract(self, logic: list[KnowledgeItem]) -> UserKnowledgeBatch: ...


def _validate_dependencies(
    dependencies: list[str], allowed: set[str], *, layer: str
) -> list[str]:
    unknown = set(dependencies) - allowed
    if unknown:
        raise ValueError(
            f"model returned unknown {layer} dependency: " + ", ".join(sorted(unknown))
        )
    return list(dict.fromkeys(dependencies))


def _validate_parent_coverage(
    items: list[KnowledgeItem], parent_ids: set[str], *, layer: str
) -> None:
    covered = {dependency for item in items for dependency in item.derived_from}
    missing = parent_ids - covered
    if missing:
        raise ValueError(
            f"model omitted {layer} parents from upward propagation: "
            + ", ".join(sorted(missing))
        )


class L3Generator:
    def __init__(self, extractor: ProductLogicExtractor) -> None:
        self._extractor = extractor

    async def generate(
        self, *, namespace: str, module: str, feature: str, l2_items: list[KnowledgeItem]
    ) -> list[KnowledgeItem]:
        batch = await self._extractor.extract(l2_items)
        allowed = {item.id for item in l2_items}
        result: list[KnowledgeItem] = []
        seen: set[str] = set()
        for draft in batch.items:
            knowledge_id = f"product.{namespace}.{draft.key}"
            if knowledge_id in seen:
                raise ValueError(f"model returned duplicate knowledge id: {knowledge_id}")
            seen.add(knowledge_id)
            result.append(
                KnowledgeItem(
                    id=knowledge_id,
                    title=draft.title.strip(),
                    layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
                    module=module,
                    feature=feature,
                    content=draft.statement.strip(),
                    status=KnowledgeStatus.PUBLISHED,
                    derived_from=_validate_dependencies(
                        draft.derived_from, allowed, layer="L2"
                    ),
                    visible_roles=list(UserRole),
                )
            )
        _validate_parent_coverage(result, allowed, layer="L2")
        return result

    async def close(self) -> None:
        close = getattr(self._extractor, "close", None)
        if close is not None:
            await close()


class L4Generator:
    def __init__(self, extractor: UserKnowledgeExtractor) -> None:
        self._extractor = extractor

    async def generate(
        self, *, namespace: str, module: str, feature: str, l3_items: list[KnowledgeItem]
    ) -> list[KnowledgeItem]:
        batch = await self._extractor.extract(l3_items)
        allowed = {item.id for item in l3_items}
        result: list[KnowledgeItem] = []
        seen: set[str] = set()
        for draft in batch.items:
            knowledge_id = f"faq.{namespace}.{draft.key}"
            if knowledge_id in seen:
                raise ValueError(f"model returned duplicate knowledge id: {knowledge_id}")
            seen.add(knowledge_id)
            result.append(
                KnowledgeItem(
                    id=knowledge_id,
                    title=draft.question.strip(),
                    layer=KnowledgeLayer.L4_USER_KNOWLEDGE,
                    module=module,
                    feature=feature,
                    content=draft.answer.strip(),
                    status=KnowledgeStatus.PUBLISHED,
                    derived_from=_validate_dependencies(
                        draft.derived_from, allowed, layer="L3"
                    ),
                    visible_roles=list(UserRole),
                )
            )
        _validate_parent_coverage(result, allowed, layer="L3")
        return result

    async def close(self) -> None:
        close = getattr(self._extractor, "close", None)
        if close is not None:
            await close()
