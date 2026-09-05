from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.knowledge import KnowledgeCatalog
from app.knowledge.models import KnowledgeItem
from app.knowledge.views import visible_items


@dataclass(frozen=True)
class RetrievalHit:
    item: KnowledgeItem
    score: float


def _char_ngrams(text: str, n: int = 2) -> Counter[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    if len(normalized) <= n:
        return Counter({normalized: 1}) if normalized else Counter()
    return Counter(normalized[i : i + n] for i in range(len(normalized) - n + 1))


def _containment(query_ngrams: Counter[str], text_ngrams: Counter[str]) -> float:
    if not query_ngrams:
        return 0.0
    matched = sum(min(count, text_ngrams[gram]) for gram, count in query_ngrams.items())
    total = sum(query_ngrams.values())
    return matched / total


def _score(question: str, item: KnowledgeItem) -> float:
    """FAQ direct-match style scoring: title weighted higher than content."""
    query_ngrams = _char_ngrams(question)
    title_score = _containment(query_ngrams, _char_ngrams(item.title))
    content_score = _containment(query_ngrams, _char_ngrams(item.content))
    return 0.6 * title_score + 0.4 * content_score


def retrieve(
    catalog: KnowledgeCatalog,
    question: str,
    role,
    top_k: int = 4,
) -> list[RetrievalHit]:
    """Retrieve role-visible knowledge assets most relevant to the question.

    Local n-gram scoring stands in for the Phase-2 vector/BM25 index; the
    function contract is the replacement point for a Qdrant-backed retriever.
    """
    candidates = visible_items(list(catalog._items.values()), role)
    ranked = sorted(
        ((_score(question, item), item) for item in candidates),
        key=lambda pair: pair[0],
        reverse=True,
    )
    hits = [RetrievalHit(item=item, score=score) for score, item in ranked if score > 0]
    return hits[:top_k]


def reciprocal_rank_fusion(ranked_ids: list[list[str]], k: int = 60) -> dict[str, float]:
    """RRF over dense (Qdrant) and sparse (local n-gram) recall lists."""
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
    """Dense (Qdrant, role-filtered server-side) + sparse (local n-gram) fused."""
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
