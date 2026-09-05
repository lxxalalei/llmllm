from __future__ import annotations

import json
from collections import Counter

from app.db.models import QueryLogRecord
from app.db.session import SessionLocal


async def record_query(
    *,
    question: str,
    role: str,
    backend: str,
    reranked: bool,
    retrieved: list[str],
    cites: list[str],
    gap: bool,
    latency_ms: int,
) -> None:
    """Persist one QA call (analytics + knowledge gap). Never breaks the QA path."""
    try:
        async with SessionLocal() as session:
            session.add(
                QueryLogRecord(
                    question=question,
                    role=role,
                    backend=backend,
                    reranked=reranked,
                    retrieved=json.dumps(retrieved, ensure_ascii=False),
                    cites=json.dumps(cites, ensure_ascii=False),
                    gap=gap,
                    latency_ms=latency_ms,
                )
            )
            await session.commit()
    except Exception:
        # analytics storage is best-effort; QA must stay available
        return None


async def list_queries(
    *,
    limit: int = 50,
    gap_only: bool = False,
    role: str | None = None,
    backend: str | None = None,
) -> list[dict[str, object]]:
    from sqlalchemy import select

    stmt = select(QueryLogRecord).order_by(QueryLogRecord.id.desc())
    if gap_only:
        stmt = stmt.where(QueryLogRecord.gap.is_(True))
    if role:
        stmt = stmt.where(QueryLogRecord.role == role)
    if backend:
        stmt = stmt.where(QueryLogRecord.backend == backend)
    async with SessionLocal() as session:
        result = await session.execute(stmt.limit(limit))
        return [_row_dict(row) for row in result.scalars().all()]


def _row_dict(row: QueryLogRecord) -> dict[str, object]:
    return {
        "id": row.id,
        "question": row.question,
        "role": row.role,
        "backend": row.backend,
        "reranked": row.reranked,
        "retrieved": json.loads(row.retrieved or "[]"),
        "cites": json.loads(row.cites or "[]"),
        "gap": row.gap,
        "latency_ms": row.latency_ms,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    gaps = [row for row in rows if row["gap"]]
    gap_count = len(gaps)
    retrieved_counter: Counter[str] = Counter()
    for row in rows:
        retrieved_counter.update(row["retrieved"])
    backend_counter = Counter(str(row["backend"]) for row in rows)
    return {
        "total": total,
        "gap_count": gap_count,
        "gap_rate": round(gap_count / total, 3) if total else 0.0,
        "backend_counts": dict(backend_counter),
        "top_retrieved": [
            {"knowledge_id": knowledge_id, "count": count}
            for knowledge_id, count in retrieved_counter.most_common(5)
        ],
        "recent_gaps": [
            {"question": row["question"], "role": row["role"], "created_at": row["created_at"]}
            for row in rows[:10]
            if row["gap"]
        ],
    }
