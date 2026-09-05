from __future__ import annotations

import uuid

from app.core.config import settings
from app.knowledge.embeddings import EmbeddingProvider
from app.knowledge.models import KnowledgeItem, UserRole
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

COLLECTION = "knowledge_assets"
_ID_NAMESPACE = uuid.NAMESPACE_URL


def _point_uuid(knowledge_id: str) -> uuid.UUID:
    return uuid.uuid5(_ID_NAMESPACE, f"llmllm:{knowledge_id}")


def _text_for(item: KnowledgeItem) -> str:
    return f"{item.title}\n{item.content}"


def role_filter(role: UserRole) -> Filter:
    """Qdrant-side role gate mirroring views.role_allows."""
    must = [FieldCondition(key="visible_roles", match=MatchValue(value=role.value))]
    if role == UserRole.USER:
        must.append(FieldCondition(key="layer", match=MatchAny(any=["L3", "L4"])))
        must.append(FieldCondition(key="status", match=MatchValue(value="published")))
    return Filter(must=must)


class KnowledgeVectorIndex:
    """Qdrant index over knowledge assets. Qdrant is an index, not the source of
    truth: full re-sync from the knowledge/ catalog keeps it consistent."""

    def __init__(self, collection_name: str = COLLECTION) -> None:
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._collection = collection_name

    async def is_available(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False

    async def ensure_collection(self, dimension: int) -> None:
        collections = await self._client.get_collections()
        names = {item.name for item in collections.collections}
        if self._collection not in names:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    async def replace_all(self, items: list[KnowledgeItem], embedder: EmbeddingProvider, batch: int = 32) -> dict[str, int]:
        """Full re-sync: embed catalog assets, upsert points, drop orphans."""
        texts = [_text_for(item) for item in items]
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch):
            vectors.extend(await embedder.embed(texts[start : start + batch]))
        if not vectors:
            return {"embedded": 0, "upserted": 0, "deleted": 0}
        dimension = len(vectors[0])
        await self.ensure_collection(dimension)

        points = []
        for item, vector in zip(items, vectors):
            payload = {
                "id": item.id,
                "layer": item.layer.value,
                "status": item.status.value,
                "module": item.module,
                "feature": item.feature,
                "visible_roles": [role.value for role in item.visible_roles],
            }
            points.append(
                PointStruct(id=_point_uuid(item.id), vector=vector, payload=payload)
            )
        await self._client.upsert(collection_name=self._collection, points=points)

        existing = await self._scroll_ids()
        local_ids = {str(_point_uuid(item.id)) for item in items}
        orphans = [point_id for point_id in existing if point_id not in local_ids]
        deleted = 0
        if orphans:
            deleted = len(orphans)
            await self._client.delete(collection_name=self._collection, points_selector=orphans)
        return {"embedded": len(items), "upserted": len(points), "deleted": deleted}

    async def _scroll_ids(self) -> list[str]:
        ids: list[str] = []
        next_offset: object = None
        while True:
            page = await self._client.scroll(
                collection_name=self._collection,
                limit=256,
                offset=next_offset,
                with_payload=False,
                with_vectors=False,
            )
            ids.extend(str(point.id) for point in page[0])
            next_offset = page[1]
            if next_offset is None:
                return ids

    async def search(
        self,
        question: str,
        embedder: EmbeddingProvider,
        role: UserRole,
        limit: int = 10,
    ) -> list[tuple[str, float]]:
        if limit <= 0:
            return []
        vector = (await embedder.embed([question]))[0]
        response = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            query_filter=role_filter(role),
            limit=limit,
            with_payload=True,
        )
        return [(hit.payload["id"], float(hit.score)) for hit in response.points]

    async def close(self) -> None:
        await self._client.close()
