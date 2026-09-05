from __future__ import annotations

import json
from typing import Protocol

from openai import AsyncOpenAI

from app.knowledge.retrieval import RetrievalHit

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance_scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "relevance": {"type": "integer", "minimum": 0, "maximum": 10},
                },
                "required": ["id", "relevance"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["relevance_scores"],
    "additionalProperties": False,
}

_RERANK_INSTRUCTIONS = (
    "Rate how relevant each supplied knowledge asset is to the user question, "
    "0 (irrelevant) to 10 (directly answers it). Use only the supplied asset ids. "
    "Return every id exactly once."
)


class Reranker(Protocol):
    async def rerank(self, question: str, hits: list[RetrievalHit]) -> list[RetrievalHit]:
        ...


class LLMReranker:
    """LLM cross-encoder-style reranker over the retrieval candidates."""

    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def rerank(self, question: str, hits: list[RetrievalHit]) -> list[RetrievalHit]:
        if len(hits) <= 1:
            return hits
        blocks = []
        for hit in hits:
            item = hit.item
            snippet = item.content if len(item.content) <= 400 else item.content[:400] + "…"
            blocks.append(f"[{item.id}] ({item.layer.value}) {item.title}\n{snippet}")
        response = await self._client.responses.create(
            model=self._model,
            instructions=_RERANK_INSTRUCTIONS,
            input=f"USER QUESTION:\n{question}\n\nKNOWLEDGE ASSETS:\n" + "\n\n".join(blocks),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "relevance_scores",
                    "schema": SCORE_SCHEMA,
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("reranker returned no structured scores")
        scores = {item["id"]: item["relevance"] for item in json.loads(response.output_text)["relevance_scores"]}
        ordered = sorted(hits, key=lambda hit: scores.get(hit.item.id, -1), reverse=True)
        return ordered

    async def close(self) -> None:
        await self._client.close()
