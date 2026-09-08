# -*- coding: utf-8 -*-
"""Serve vs Review mode contracts for QA retrieval."""
from pathlib import Path

from app.knowledge import KnowledgeCatalog, UserRole
from app.knowledge.retrieval import retrieve
from app.knowledge.vector_index import role_filter


def test_serve_retrieval_excludes_unpublished_for_every_role() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(catalog, "怎么给频道添加成员？谁能把用户加入频道？", UserRole.PRODUCT, top_k=8)
    assert hits, "expected some hit"
    assert all(h.item.status.value == "published" for h in hits), (
        [h.item.id for h in hits if h.item.status.value != "published"]
    )


def test_review_mode_retrieval_includes_review_assets() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(
        catalog,
        "怎么给频道添加成员？谁能把用户加入频道？",
        UserRole.PRODUCT,
        top_k=8,
        review_mode=True,
    )
    review_hits = [h.item.id for h in hits if h.item.status.value == "review"]
    assert review_hits, "review mode must surface review assets"
    assert any("membership" in hid for hid in review_hits)


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
