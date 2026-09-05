from __future__ import annotations

from openai import AsyncOpenAI

from app.code_index import Symbol
from app.knowledge.l1_generator import EngineeringFactBatch
from app.knowledge.l2_generator import EngineeringRuleBatch
from app.knowledge.models import KnowledgeItem


def _statement(item: KnowledgeItem) -> str:
    lines = item.content.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


class OpenAIEngineeringFactExtractor:
    """Extract code facts with OpenAI Structured Outputs.

    The model only proposes semantic facts. Repo/ref/file/symbol bindings are
    validated and attached by L1Generator.
    """

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def _extract(
        self,
        symbols: list[Symbol],
        existing_facts: list[KnowledgeItem] | None = None,
    ) -> EngineeringFactBatch:
        if not symbols:
            return EngineeringFactBatch(facts=[])

        source_blocks = []
        for symbol in symbols:
            source_blocks.append(
                f"SYMBOL: {symbol.name}\nLINES: {symbol.start_line}-{symbol.end_line}\n```\n{symbol.source}\n```"
            )

        existing_block = ""
        if existing_facts:
            existing_lines = []
            for item in existing_facts:
                key = item.id.rsplit(".", 1)[-1]
                symbol = item.sources[0].symbol if item.sources else None
                existing_lines.append(
                    f"KEY: {key}\nSYMBOL: {symbol or '-'}\nTITLE: {item.title}\nFACT: {_statement(item)}"
                )
            existing_block = (
                "\n\nEXISTING FACTS FROM THE PREVIOUS CODE VERSION:\n"
                + "\n\n".join(existing_lines)
            )

        instructions = (
            "You extract L1 engineering facts from source code. "
            "Return only facts explicitly supported by the supplied code. "
            "Do not infer product intent, user expectations, or undocumented behavior. "
            "Each fact must be independently useful, concise, and non-duplicative. "
            "Use only one of the supplied symbol names in each fact.symbol. "
            "Use a stable lowercase snake_case key describing the fact."
        )
        if existing_facts:
            instructions += (
                " Existing facts are from the previous code version. "
                "When the same semantic fact is still supported, reuse its exact existing KEY. "
                "Omit an existing key when that fact is no longer supported. "
                "Use a new key only for a genuinely new fact."
            )

        response = await self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input="\n\n".join(source_blocks) + existing_block,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "engineering_fact_batch",
                    "schema": EngineeringFactBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured engineering facts")
        return EngineeringFactBatch.model_validate_json(response.output_text)

    async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch:
        return await self._extract(symbols)

    async def extract_incremental(
        self,
        symbols: list[Symbol],
        existing_facts: list[KnowledgeItem],
    ) -> EngineeringFactBatch:
        return await self._extract(symbols, existing_facts)

    async def close(self) -> None:
        """Close the underlying HTTP client (required before asyncio loop shutdown)."""
        await self._client.close()


class OpenAIEngineeringRuleExtractor:
    """Synthesize L2 engineering rules from the current L1 feature scope."""

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def extract(
        self,
        facts: list[KnowledgeItem],
        existing_rules: list[KnowledgeItem],
    ) -> EngineeringRuleBatch:
        if not facts:
            return EngineeringRuleBatch(rules=[])

        fact_blocks = [
            f"ID: {item.id}\nTITLE: {item.title}\nFACT: {_statement(item)}"
            for item in facts
        ]
        existing_block = ""
        if existing_rules:
            rule_blocks = []
            for item in existing_rules:
                key = item.id.rsplit(".", 1)[-1]
                rule_blocks.append(
                    f"KEY: {key}\nTITLE: {item.title}\nRULE: {_statement(item)}\n"
                    f"DERIVED_FROM: {', '.join(item.derived_from)}"
                )
            existing_block = (
                "\n\nEXISTING L2 RULES FROM THE PREVIOUS KNOWLEDGE VERSION:\n"
                + "\n\n".join(rule_blocks)
            )

        response = await self._client.responses.create(
            model=self._model,
            instructions=(
                "You synthesize L2 engineering rules from supplied L1 engineering facts. "
                "Rules are developer-facing technical/domain rules, not product intent or user documentation. "
                "Every derived_from id must be one of the supplied L1 IDs. "
                "Existing rules are from the previous knowledge version. "
                "If the same engineering rule remains supported, reuse its exact existing KEY. "
                "Omit rules no longer supported and add a new key only for a genuinely new rule. "
                "Prefer a small set of useful, non-duplicative rules."
            ),
            input="CURRENT L1 FACTS:\n\n" + "\n\n".join(fact_blocks) + existing_block,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "engineering_rule_batch",
                    "schema": EngineeringRuleBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured engineering rules")
        return EngineeringRuleBatch.model_validate_json(response.output_text)

    async def close(self) -> None:
        await self._client.close()
