from fastapi import APIRouter, HTTPException, Query

from app.knowledge.analytics import list_queries, summarize

router = APIRouter(tags=["analytics"])


@router.get("/queries")
async def query_analytics(
    limit: int = Query(default=50, ge=1, le=500),
    gap_only: bool = False,
    role: str | None = None,
    backend: str | None = None,
) -> dict[str, object]:
    try:
        queries = await list_queries(limit=limit, gap_only=gap_only, role=role, backend=backend)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"analytics store unavailable: {exc}") from exc
    return {"queries": queries, "summary": summarize(queries)}
