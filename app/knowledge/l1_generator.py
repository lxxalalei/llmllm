from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.code_index import Symbol
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, SourceBinding, UserRole


class EngineeringFactDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    symbol: str
    title: str
    statement: str


class EngineeringFactBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[EngineeringFactDraft]


class EngineeringFactExtractor(Protocol):
    async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch: ...


class L1Generator:
    """Convert model-extracted engineering facts into authoritative L1 draft objects.

    Source identity is supplied by code, never invented by the model. During
    incremental regeneration an extractor may expose ``extract_incremental``;
    existing facts are then supplied so stable keys can be reused.
    """

    def __init__(self, extractor: EngineeringFactExtractor) -> None:
        self._extractor = extractor

    async def generate(
        self,
        *,
        namespace: str,
        module: str,
        feature: str,
        repo: str,
        ref: str | None,
        commit: str | None,
        file: str,
        symbols: list[Symbol],
        existing_items: list[KnowledgeItem] | None = None,
    ) -> list[KnowledgeItem]:
        if not symbols:
            return []

        if existing_items:
            extract_incremental = getattr(self._extractor, "extract_incremental", None)
            if extract_incremental is None:
                raise ValueError("engineering fact extractor does not support incremental regeneration")
            batch = await extract_incremental(symbols, existing_items)
        else:
            batch = await self._extractor.extract(symbols)

        symbol_map = {symbol.name: symbol for symbol in symbols}
        items: list[KnowledgeItem] = []
        seen_ids: set[str] = set()

        for fact in batch.facts:
            symbol = symbol_map.get(fact.symbol)
            if symbol is None:
                raise ValueError(f"model returned unknown source symbol: {fact.symbol}")

            knowledge_id = f"eng.{namespace}.{fact.key}"
            if knowledge_id in seen_ids:
                raise ValueError(f"model returned duplicate knowledge id: {knowledge_id}")
            seen_ids.add(knowledge_id)

            items.append(
                KnowledgeItem(
                    id=knowledge_id,
                    title=fact.title.strip(),
                    layer=KnowledgeLayer.L1_ENGINEERING_FACT,
                    module=module,
                    feature=feature,
                    content=fact.statement.strip(),
                    status=KnowledgeStatus.DRAFT,
                    sources=[
                        SourceBinding(
                            repo=repo,
                            ref=ref,
                            commit=commit,
                            file=file,
                            symbol=symbol.name,
                            start_line=symbol.start_line,
                            end_line=symbol.end_line,
                        )
                    ],
                    visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
                )
            )

        return items

    async def close(self) -> None:
        """Close the underlying extractor client if it exposes one."""
        close = getattr(self._extractor, "close", None)
        if close is not None:
            await close()
