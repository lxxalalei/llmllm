from fastapi import APIRouter

from app.knowledge.models import (
    KnowledgeItem,
    KnowledgeLayer,
    KnowledgeStatus,
    SourceBinding,
    UserRole,
)

router = APIRouter()


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
