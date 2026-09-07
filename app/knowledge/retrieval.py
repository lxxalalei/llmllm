from __future__ import annotations

from dataclasses import dataclass

from app.knowledge import KnowledgeCatalog
from app.knowledge.bm25 import BM25Index
from app.knowledge.models import KnowledgeItem
from app.knowledge.views import role_allows, visible_items


@dataclass(frozen=True)
class RetrievalHit:
    item: KnowledgeItem
    score: float


def _text_of(item: KnowledgeItem) -> str:
    return f"{item.title}\n{item.content}"


def retrieve(
    catalog: KnowledgeCatalog,
    question: str,
    role,
    top_k: int = 4,
    *,
    review_mode: bool = False,
) -> list[RetrievalHit]:
    """Sparse (BM25) retrieval over role-visible knowledge assets.

    Normal retrieval only sees Published assets. Knowledge-review tooling must
    opt in explicitly with ``review_mode=True``.
    """
    candidates = visible_items(
        list(catalog._items.values()),
        role,
        include_unpublished=review_mode,
    )
    if not candidates:
        return []
    index = BM25Index([(_text_of(item), item) for item in candidates])
    scored = index.search(question, top_k)
    return [RetrievalHit(item=item, score=score) for score, item in scored]


def reciprocal_rank_fusion(ranked_ids: list[list[str]], k: int = 60) -> dict[str, float]:
    """RRF over dense (Qdrant) and sparse (BM25) recall lists."""
    scores: dict[str, float] = {}
    for ranks in ranked_ids:
        for position, knowledge_id in enumerate(ranks):
            scores[knowledge_id] = scores.get(knowledge_id, 0.0) + 1.0 / (k + position + 1)
    return dict(sorted(scores.items(), key=lambda pair: pair[1], reverse=True))


async def retrieve_hybrid(
    catalog: KnowledgeCatalog,
    question: str,
    role,
    vector_index,
    embedder,
    top_k: int = 4,
    *,
    review_mode: bool = False,
) -> list[RetrievalHit]:
    """Dense + sparse retrieval with the same serve/review visibility policy."""
    dense = await vector_index.search(question, embedder, role, limit=top_k * 3)
    dense_ids = [knowledge_id for knowledge_id, _score in dense]
    sparse = retrieve(
        catalog,
        question,
        role,
        top_k=top_k * 3,
        review_mode=review_mode,
    )
    sparse_ids = [hit.item.id for hit in sparse]
    fused = reciprocal_rank_fusion([dense_ids, sparse_ids])
    hits = []
    for knowledge_id, score in fused.items():
        try:
            item = catalog.get(knowledge_id)
        except KeyError:
            continue  # stale index entry
        if not role_allows(role, item, include_unpublished=review_mode):
            continue
        hits.append(RetrievalHit(item=item, score=score))
        if len(hits) >= top_k:
            break
    return hits
