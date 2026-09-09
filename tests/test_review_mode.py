# -*- coding: utf-8 -*-
"""Serve vs Review mode contracts for QA retrieval."""
from pathlib import Path

from app.knowledge import KnowledgeCatalog, UserRole
from app.knowledge.assets import KnowledgeCatalog as KC
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus
from app.knowledge.retrieval import retrieve
from app.knowledge.vector_index import role_filter


def _item(knowledge_id: str, status: KnowledgeStatus, layer: KnowledgeLayer, roles) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title="Channel permission",
        layer=layer,
        module="mattermost.channel",
        feature="channel_permission",
        content="Channel permission rule.",
        status=status,
        visible_roles=roles,
    )


def test_serve_retrieval_excludes_unpublished_for_every_role() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(catalog, "怎么给频道添加成员？谁能把用户加入频道？", UserRole.PRODUCT, top_k=8)
    assert hits, "expected some hit"
    assert all(h.item.status.value == "published" for h in hits), (
        [h.item.id for h in hits if h.item.status.value != "published"]
    )


def test_review_mode_retrieval_includes_unpublished_assets_explicitly() -> None:
    catalog = KC(
        [
            _item("product.published", KnowledgeStatus.PUBLISHED, KnowledgeLayer.L3_PRODUCT_LOGIC, [UserRole.PRODUCT]),
            _item("product.review", KnowledgeStatus.REVIEW, KnowledgeLayer.L3_PRODUCT_LOGIC, [UserRole.PRODUCT]),
        ]
    )
    serve_hits = retrieve(catalog, "Channel permission", UserRole.PRODUCT, top_k=10)
    assert [h.item.id for h in serve_hits] == ["product.published"]

    review_hits = retrieve(catalog, "Channel permission", UserRole.PRODUCT, top_k=10, review_mode=True)
    assert {h.item.id for h in review_hits} == {"product.published", "product.review"}


def test_dense_role_filter_serves_only_published_outside_review() -> None:
    f_serve = role_filter(UserRole.PRODUCT, include_unpublished=False)
    statuses = [m for m in f_serve.must if m.key == "status"]
    assert statuses and statuses[0].match.value == "published"
    f_review = role_filter(UserRole.PRODUCT, include_unpublished=True)
    statuses_review = [m for m in f_review.must if m.key == "status"]
    assert not statuses_review
    # user is never allowed review-mode material
    f_user = role_filter(UserRole.USER, include_unpublished=True)
    assert any(m.key == "status" and m.match.value == "published" for m in f_user.must)
