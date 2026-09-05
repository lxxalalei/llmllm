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
