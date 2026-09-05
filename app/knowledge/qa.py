from __future__ import annotations

import json
from typing import Protocol

from openai import AsyncOpenAI

from app.knowledge import KnowledgeCatalog
from app.knowledge.retrieval import RetrievalHit

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "cites": {"type": "array", "items": {"type": "string"}},
        "knowledge_gap": {"type": "boolean"},
    },
    "required": ["answer", "cites", "knowledge_gap"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTIONS = (
    "You are the enterprise product knowledge assistant. Answer ONLY from the "
    "supplied knowledge assets. Ground every claim in at least one supplied asset "
    "and cite its knowledge id in cites. If no supplied asset covers the question, "
    "set knowledge_gap to true and do not invent content. Match the language of "
    "the user question."
)


class QAResponder(Protocol):
    async def answer(self, question: str, context: list[RetrievalHit]) -> dict[str, object]:
        ...


def render_context(hits: list[RetrievalHit]) -> str:
    blocks = []
    for hit in hits:
        item = hit.item
        source_lines = []
        for source in item.sources:
            source_lines.append(
                f"repo={source.repo} commit={source.commit or '-'} file={source.file} "
                f"symbol={source.symbol or '-'} lines={source.start_line}-{source.end_line}"
            )
        binding = "\n".join(f"    source: {line}" for line in source_lines)
        blocks.append(
            f"[{item.id}] ({item.layer.value}/{item.status.value}) {item.title}\n"
            f"{item.content}\n{binding}".rstrip()
        )
    return "\n\n".join(blocks)


class OpenAIQAResponder:
    """Structured-answer responder over the same OpenAI-compatible endpoint used
    by the L1 generator (OPENAI_BASE_URL / LLM_API_KEY / LLM_MODEL)."""

    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def answer(self, question: str, context: list[RetrievalHit]) -> dict[str, object]:
        if not context:
            return {"answer": "知识库暂无覆盖该问题的已发布内容。", "cites": [], "knowledge_gap": True}
        response = await self._client.responses.create(
            model=self._model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=f"USER QUESTION:\n{question}\n\nKNOWLEDGE ASSETS:\n{render_context(context)}",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "qa_answer",
                    "schema": ANSWER_SCHEMA,
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("QA model returned no structured answer")
        return json.loads(response.output_text)

    async def close(self) -> None:
        await self._client.close()


async def answer_question(
    *,
    catalog: KnowledgeCatalog,
    question: str,
    role,
    responder: QAResponder,
    top_k: int = 4,
    backend: str = "local",
    vector_index=None,
    embedder=None,
    reranker=None,
) -> dict[str, object]:
    """Answer with the requested retrieval backend.

    hybrid = Qdrant dense (role-filtered) fused with BM25 sparse via RRF;
    any hybrid failure falls back to the local retriever and reports the
    backend actually used. When a reranker is supplied, candidates are
    retrieved wider (2x top_k), reranked, then cut back to top_k.
    """
    hits = None
    used_backend = "local"
    used_rerank = False
    candidate_k = top_k * 2 if reranker is not None else top_k
    if backend == "hybrid" and vector_index is not None and embedder is not None:
        try:
            from app.knowledge.retrieval import retrieve_hybrid

            hits = await retrieve_hybrid(
                catalog, question, role, vector_index, embedder, top_k=candidate_k
            )
            used_backend = "hybrid"
        except Exception:
            hits = None
    if hits is None:
        from app.knowledge.retrieval import retrieve

        hits = retrieve(catalog, question, role, top_k=candidate_k)
        used_backend = "local"
    if reranker is not None and hits:
        try:
            hits = await reranker.rerank(question, hits)
            used_rerank = True
        except Exception:
            used_rerank = False
        hits = hits[:top_k]

    retrieved = [hit.item.id for hit in hits]
    result = await responder.answer(question, hits)
    # citation hardening: only ids that were actually supplied may be cited
    known = set(retrieved)
    cites = [cite for cite in result.get("cites", []) if cite in known]
    return {
        "answer": result.get("answer", ""),
        "cites": cites,
        "knowledge_gap": bool(result.get("knowledge_gap", False)),
        "retrieved": retrieved,
        "backend": used_backend,
        "reranked": used_rerank,
    }
