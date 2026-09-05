from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.knowledge import KnowledgeCatalog
from app.knowledge.models import UserRole
from app.knowledge.qa import OpenAIQAResponder, answer_question

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


def _build_responder() -> OpenAIQAResponder | None:
    if settings.llm_provider != "openai" or not settings.llm_api_key or not settings.llm_model:
        return None
    return OpenAIQAResponder(api_key=settings.llm_api_key, model=settings.llm_model)


@router.post("", response_model=QaResponse)
async def qa(payload: QaRequest) -> QaResponse:
    responder = _build_responder()
    if responder is None:
        raise HTTPException(
            status_code=503,
            detail="LLM not configured: set LLM_PROVIDER=openai, LLM_API_KEY and LLM_MODEL",
        )
    catalog = KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)
    try:
        result = await answer_question(
            catalog=catalog,
            question=payload.question,
            role=payload.role,
            responder=responder,
            top_k=payload.top_k,
        )
    finally:
        await responder.close()

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
    return QaResponse(
        answer=result["answer"],
        cites=cites,
        knowledge_gap=result["knowledge_gap"],
        retrieved=result["retrieved"],
    )
