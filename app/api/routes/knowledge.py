from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.knowledge import KnowledgeCatalog
from app.knowledge.models import (
    KnowledgeItem,
    KnowledgeLayer,
    KnowledgeStatus,
    SourceBinding,
    UserRole,
)

router = APIRouter()
KNOWLEDGE_ROOT = Path("knowledge")


class KnowledgeLineageResponse(BaseModel):
    knowledge_id: str
    lineage: list[KnowledgeItem]
    sources: list[SourceBinding]


def _catalog() -> KnowledgeCatalog:
    return KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)


@router.get("/example", response_model=KnowledgeItem)
async def example_knowledge_item() -> KnowledgeItem:
    return KnowledgeItem(
        id="product.conversation.work_order.auto_archive",
        title="工单会话自动归档",
        layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
        module="conversation",
        feature="work_order",
        content="已结束且长期无活动的工单会话会自动进入归档状态。",
        status=KnowledgeStatus.PUBLISHED,
        derived_from=["eng.conversation.work_order.archive"],
        sources=[
            SourceBinding(
                repo="example/mars-server",
                file="src/conversation/archive_service.py",
                symbol="archive_if_inactive",
            )
        ],
        visible_roles=[UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER],
    )


@router.get("/{knowledge_id}/lineage", response_model=KnowledgeLineageResponse)
async def knowledge_lineage(knowledge_id: str) -> KnowledgeLineageResponse:
    catalog = _catalog()
    try:
        lineage = catalog.trace_lineage(knowledge_id)
        sources = catalog.trace_sources(knowledge_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return KnowledgeLineageResponse(knowledge_id=knowledge_id, lineage=lineage, sources=sources)


@router.get("/{knowledge_id}", response_model=KnowledgeItem)
async def knowledge_item(knowledge_id: str) -> KnowledgeItem:
    try:
        return _catalog().get(knowledge_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
