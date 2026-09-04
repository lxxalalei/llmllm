from fastapi import APIRouter

from app.retrieval.qdrant import QdrantSearchIndex

router = APIRouter(tags=["system"])


@router.get("/ready")
async def ready() -> dict[str, object]:
    qdrant = QdrantSearchIndex()
    qdrant_ok = await qdrant.is_available()
    return {
        "status": "ready" if qdrant_ok else "degraded",
        "dependencies": {"qdrant": qdrant_ok},
    }
