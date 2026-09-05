from __future__ import annotations

from typing import Protocol

from openai import AsyncOpenAI


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class OpenAIEmbeddingProvider:
    """OpenAI-compatible /embeddings provider (e.g. GLM/Embedding-3 over the
    configured base URL). Shares the LLM credential/endpoint environment."""

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(model=self.model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    async def close(self) -> None:
        await self._client.close()
