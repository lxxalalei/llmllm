from __future__ import annotations

from openai import AsyncOpenAI

from app.code_index import Symbol
from app.knowledge.l1_generator import EngineeringFactBatch


class OpenAIEngineeringFactExtractor:
    """Extract code facts with OpenAI Structured Outputs.

    The model only proposes semantic facts. Repo/ref/file/symbol bindings are
    validated and attached by L1Generator.
    """

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch:
        if not symbols:
            return EngineeringFactBatch(facts=[])

        source_blocks = []
        for symbol in symbols:
            source_blocks.append(
                f"SYMBOL: {symbol.name}\nLINES: {symbol.start_line}-{symbol.end_line}\n```\n{symbol.source}\n```"
            )

        response = await self._client.responses.create(
            model=self._model,
            instructions=(
                "You extract L1 engineering facts from source code. "
                "Return only facts explicitly supported by the supplied code. "
                "Do not infer product intent, user expectations, or undocumented behavior. "
                "Each fact must be independently useful, concise, and non-duplicative. "
                "Use only one of the supplied symbol names in each fact.symbol. "
                "Use a stable lowercase snake_case key describing the fact."
            ),
            input="\n\n".join(source_blocks),
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

    async def close(self) -> None:
        """Close the underlying HTTP client (required before asyncio loop shutdown)."""
        await self._client.close()
