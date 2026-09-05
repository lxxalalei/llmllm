from __future__ import annotations

from dataclasses import dataclass

from app.knowledge import KnowledgeCatalog
from app.knowledge.bm25 import BM25Index
from app.knowledge.models import KnowledgeItem
from app.knowledge.views import visible_items


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
) -> list[RetrievalHit]:
    """Sparse (BM25) retrieval over role-visible knowledge assets.

    The function contract is the replacement point for a Qdrant-backed
    retriever; dense retrieval lives in retrieve_hybrid below.
    """
    candidates = visible_items(list(catalog._items.values()), role)
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
) -> list[RetrievalHit]:
    """Dense (Qdrant, role-filtered server-side) + sparse (BM25) fused via RRF."""
    dense = await vector_index.search(question, embedder, role, limit=top_k * 3)
    dense_ids = [knowledge_id for knowledge_id, _score in dense]
    sparse = retrieve(catalog, question, role, top_k=top_k * 3)
    sparse_ids = [hit.item.id for hit in sparse]
    fused = reciprocal_rank_fusion([dense_ids, sparse_ids])
    hits = []
    for knowledge_id, score in fused.items():
        try:
            item = catalog.get(knowledge_id)
        except KeyError:
            continue  # stale index entry
        hits.append(RetrievalHit(item=item, score=score))
        if len(hits) >= top_k:
            break
    return hits
