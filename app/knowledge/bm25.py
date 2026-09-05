from __future__ import annotations

import math
import re
from collections import Counter

_ASCII_TOKEN = re.compile(r"[a-z0-9]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """CJK bigrams + ascii word tokens (lowercased)."""
    lowered = text.lower()
    tokens: list[str] = []
    for word in _ASCII_TOKEN.findall(lowered):
        if len(word) > 1:
            tokens.append(word)
    for run in _CJK_RUN.findall(lowered):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


class BM25Index:
    """Lightweight in-memory BM25 (k1=1.5, b=0.75) over a small doc set.

    Built per query over the role-visible catalog slice; stands in for a
    dedicated sparse index until Phase 3 scale work."""
    def __init__(self, docs: list[tuple[str, object]], k1: float = 1.5, b: float = 0.75) -> None:
        self._docs = docs
        self._k1 = k1
        self._b = b
        self._doc_count = len(docs)
        self._doc_lengths: list[int] = []
        self._doc_freq: Counter[str] = Counter()
        self._term_counts: list[Counter[str]] = []
        for text, _item in docs:
            counts = Counter(tokenize(text))
            self._term_counts.append(counts)
            self._doc_lengths.append(sum(counts.values()))
            for term in counts:
                self._doc_freq[term] += 1
        self._avgdl = sum(self._doc_lengths) / self._doc_count if self._doc_count else 0.0

    def _idf(self, term: str) -> float:
        df = self._doc_freq[term]
        return math.log(1 + (self._doc_count - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int) -> list[tuple[float, object]]:
        query_terms = Counter(tokenize(query))
        scored: list[tuple[float, int]] = []
        for doc_index in range(self._doc_count):
            length = self._doc_lengths[doc_index]
            denominator = self._k1 * (1 - self._b + self._b * (length / self._avgdl if self._avgdl else 1.0))
            score = 0.0
            for term, qty in query_terms.items():
                tf = self._term_counts[doc_index].get(term, 0)
                if not tf:
                    continue
                idf = self._idf(term)
                score += qty * idf * (tf * (self._k1 + 1)) / (tf + denominator)
            if score > 0:
                scored.append((score, doc_index))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [(score, self._docs[doc_index][1]) for score, doc_index in scored[:top_k]]
