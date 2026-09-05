from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import time

from app.core.config import settings
from app.knowledge import KnowledgeCatalog
from app.knowledge.analytics import record_query
from app.knowledge.models import UserRole
from app.knowledge.embeddings import OpenAIEmbeddingProvider
from app.knowledge.qa import OpenAIQAResponder, answer_question
from app.knowledge.rerank import LLMReranker
from app.knowledge.vector_index import KnowledgeVectorIndex

router = APIRouter()
KNOWLEDGE_ROOT = Path("knowledge")


class QaRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    role: UserRole = UserRole.USER
    top_k: int = Field(default=4, ge=1, le=8)


class Cite(BaseModel):
    id: str
    title: str
    layer: str
    status: str


class QaResponse(BaseModel):
    answer: str
    cites: list[Cite]
    knowledge_gap: bool
    retrieved: list[str]
    backend: str
    reranked: bool


def _build_responder() -> OpenAIQAResponder | None:
    if settings.llm_provider != "openai" or not settings.llm_api_key or not settings.llm_model:
        return None
    return OpenAIQAResponder(api_key=settings.llm_api_key, model=settings.llm_model)


def _build_reranker() -> LLMReranker | None:
    if not settings.rerank or not settings.llm_api_key or not settings.llm_model:
        return None
    return LLMReranker(api_key=settings.llm_api_key, model=settings.llm_model)


@router.post("", response_model=QaResponse)
async def qa(payload: QaRequest) -> QaResponse:
    responder = _build_responder()
    if responder is None:
        raise HTTPException(
            status_code=503,
            detail="LLM not configured: set LLM_PROVIDER=openai, LLM_API_KEY and LLM_MODEL",
        )
    catalog = KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)
    backend = settings.retrieval_backend
    embedder = None
    vector_index = None
    reranker = _build_reranker()
    if backend == "hybrid" and settings.embedding_model and settings.llm_api_key:
        embedder = OpenAIEmbeddingProvider(
            api_key=settings.llm_api_key, model=settings.embedding_model
        )
        vector_index = KnowledgeVectorIndex()
    started = time.monotonic()
    try:
        result = await answer_question(
            catalog=catalog,
            question=payload.question,
            role=payload.role,
            responder=responder,
            top_k=payload.top_k,
            backend=backend,
            vector_index=vector_index,
            embedder=embedder,
            reranker=reranker,
        )
    finally:
        await responder.close()
        if embedder is not None:
            await embedder.close()
        if vector_index is not None:
            await vector_index.close()
        if reranker is not None:
            await reranker.close()

    by_id = {item.id: item for item in catalog._items.values()}
    cites = [
        Cite(
            id=cite_id,
            title=by_id[cite_id].title,
            layer=by_id[cite_id].layer.value,
            status=by_id[cite_id].status.value,
        )
        for cite_id in result["cites"]
        if cite_id in by_id
    ]
    latency_ms = int((time.monotonic() - started) * 1000)
    await record_query(
        question=payload.question,
        role=payload.role.value,
        backend=result["backend"],
        reranked=result["reranked"],
        retrieved=result["retrieved"],
        cites=[cite.id for cite in cites],
        gap=result["knowledge_gap"],
        latency_ms=latency_ms,
    )
    return QaResponse(
        answer=result["answer"],
        cites=cites,
        knowledge_gap=result["knowledge_gap"],
        retrieved=result["retrieved"],
        backend=result["backend"],
        reranked=result["reranked"],
    )
