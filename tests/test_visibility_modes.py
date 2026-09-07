from app.knowledge.assets import KnowledgeCatalog
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.retrieval import retrieve


def _item(knowledge_id: str, status: KnowledgeStatus) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title="Channel permission",
        layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
        module="mattermost.channel",
        feature="channel_permission",
        content="Channel permission rule.",
        status=status,
        visible_roles=[UserRole.PRODUCT],
    )


def test_normal_retrieval_excludes_review_assets_for_product_role() -> None:
    catalog = KnowledgeCatalog(
        [
            _item("product.published", KnowledgeStatus.PUBLISHED),
            _item("product.review", KnowledgeStatus.REVIEW),
        ]
    )

    hits = retrieve(catalog, "Channel permission", UserRole.PRODUCT, top_k=10)

    assert [hit.item.id for hit in hits] == ["product.published"]


def test_review_mode_can_retrieve_unpublished_assets_explicitly() -> None:
    catalog = KnowledgeCatalog(
        [
            _item("product.published", KnowledgeStatus.PUBLISHED),
            _item("product.review", KnowledgeStatus.REVIEW),
        ]
    )

    hits = retrieve(
        catalog,
        "Channel permission",
        UserRole.PRODUCT,
        top_k=10,
        review_mode=True,
    )

    assert {hit.item.id for hit in hits} == {"product.published", "product.review"}
