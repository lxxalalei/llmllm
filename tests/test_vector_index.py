import asyncio
import hashlib
import uuid

import pytest

from app.core.config import settings
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.retrieval import reciprocal_rank_fusion, retrieve
from app.knowledge.vector_index import KnowledgeVectorIndex

try:
    from qdrant_client import QdrantClient as SyncQdrantClient

    _probe = SyncQdrantClient(url=settings.qdrant_url, timeout=2)
    _probe.get_collections()
    _probe.close()
    QDRANT_UP = True
except Exception:
    QDRANT_UP = False

pytestmark = pytest.mark.skipif(not QDRANT_UP, reason="Qdrant not reachable")


def _hash_vector(text: str, dim: int = 8) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [(digest[i % len(digest)] / 255.0) - 0.5 for i in range(dim)]
    return vector


class _FakeEmbedder:
    def __init__(self, dim: int = 8) -> None:
        self.dim = dim
        self.calls: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.extend(texts)
        return [_hash_vector(text, self.dim) for text in texts]

    async def close(self) -> None:
        return None


def _item(
    item_id: str,
    layer: KnowledgeLayer,
    status: KnowledgeStatus,
    roles: list[UserRole],
    content: str = "body text",
) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=layer,
        module="m",
        content=content,
        status=status,
        visible_roles=roles,
    )


def test_reciprocal_rank_fusion() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["c", "a"]], k=60)
    assert list(fused)[0] == "a"
    assert fused["b"] > 0.0


def test_hybrid_fusion_uses_local_sparse_on_ci() -> None:
    from pathlib import Path

    from app.knowledge import KnowledgeCatalog

    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(catalog, "为什么我不能继续创建频道？", UserRole.USER, top_k=3)
    assert hits[0].item.id == "faq.mattermost.channel.create.limit"


@pytest.mark.asyncio
async def test_index_sync_search_and_role_filter() -> None:
    collection = "test_knowledge_" + uuid.uuid4().hex[:10]
    index = KnowledgeVectorIndex(collection_name=collection)
    embedder = _FakeEmbedder()
    items = [
        _item(
            "faq.demo.limit",
            KnowledgeLayer.L4_USER_KNOWLEDGE,
            KnowledgeStatus.PUBLISHED,
            [UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER],
            content="团队频道数量达到上限后不能继续创建新频道。",
        ),
        _item(
            "eng.demo.rule",
            KnowledgeLayer.L2_ENGINEERING_RULE,
            KnowledgeStatus.DRAFT,
            [UserRole.DEVELOPER, UserRole.TEST, UserRole.PRODUCT],
            content="创建前检查当前团队频道数是否超过 MaxChannelsPerTeam。",
        ),
    ]
    try:
        result = await index.replace_all(items, embedder)
        assert result["upserted"] == 2

        user_hits = await index.search("频道数量上限", embedder, UserRole.USER, limit=10)
        user_ids = {hit_id for hit_id, _score in user_hits}
        assert "faq.demo.limit" in user_ids
        assert "eng.demo.rule" not in user_ids  # user must not see L2

        product_hits = await index.search("MaxChannelsPerTeam 检查", embedder, UserRole.PRODUCT, limit=10)
        product_ids = {hit_id for hit_id, _score in product_hits}
        assert "eng.demo.rule" in product_ids

        # orphan cleanup on re-sync
        result2 = await index.replace_all([items[0]], embedder)
        assert result2["deleted"] == 1
    finally:
        await index.close()
        _sync = SyncQdrantClient(url=settings.qdrant_url, timeout=5)
        _sync.delete_collection(collection)
        _sync.close()
