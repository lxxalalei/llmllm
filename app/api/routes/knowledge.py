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
from app.knowledge.views import drill_down, role_allows, visible_items

router = APIRouter()
KNOWLEDGE_ROOT = Path("knowledge")


class KnowledgeLineageResponse(BaseModel):
    knowledge_id: str
    lineage: list[KnowledgeItem]
    sources: list[SourceBinding]


def _catalog() -> KnowledgeCatalog:
    return KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)


def _get_visible(catalog: KnowledgeCatalog, knowledge_id: str, role: UserRole | None) -> KnowledgeItem:
    try:
        item = catalog.get(knowledge_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if role is not None and not role_allows(role, item):
        # do not reveal existence to roles that cannot consume the item
        raise HTTPException(status_code=404, detail=f"unknown knowledge id: {knowledge_id}")
    return item


@router.get("", response_model=list[KnowledgeItem])
async def list_knowledge(role: UserRole | None = None) -> list[KnowledgeItem]:
    catalog = _catalog()
    items = sorted(catalog._items.values(), key=lambda item: item.id)
    if role is not None:
        items = visible_items(items, role)
    return items


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


@router.get("/{knowledge_id}/drill", response_model=list[KnowledgeItem])
async def knowledge_drill(knowledge_id: str, role: UserRole | None = None) -> list[KnowledgeItem]:
    catalog = _catalog()
    item = _get_visible(catalog, knowledge_id, role)
    return drill_down(catalog, item, role)


@router.get("/{knowledge_id}/lineage", response_model=KnowledgeLineageResponse)
async def knowledge_lineage(knowledge_id: str, role: UserRole | None = None) -> KnowledgeLineageResponse:
    catalog = _catalog()
    item = _get_visible(catalog, knowledge_id, role)
    try:
        lineage = catalog.trace_lineage(item.id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if role is not None:
        lineage = [node for node in lineage if role_allows(role, node)]

    # SourceBinding is code-level evidence. Only collect bindings from lineage
    # nodes the selected role can consume, so a user-visible FAQ cannot expose
    # hidden L1/L2 code evidence through the lineage endpoint.
    sources: list[SourceBinding] = []
    seen: set[tuple[str, str | None, str | None, str, str | None]] = set()
    for node in lineage:
        for source in node.sources:
            key = (source.repo, source.ref, source.commit, source.file, source.symbol)
            if key in seen:
                continue
            seen.add(key)
            sources.append(source)

    return KnowledgeLineageResponse(knowledge_id=knowledge_id, lineage=lineage, sources=sources)


@router.get("/{knowledge_id}", response_model=KnowledgeItem)
async def knowledge_item(knowledge_id: str, role: UserRole | None = None) -> KnowledgeItem:
    return _get_visible(_catalog(), knowledge_id, role)
