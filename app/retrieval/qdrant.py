from qdrant_client import AsyncQdrantClient

from app.core.config import settings


class QdrantSearchIndex:
    def __init__(self) -> None:
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )

    async def is_available(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False
