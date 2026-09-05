from types import SimpleNamespace

import pytest

from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.vector_index import KnowledgeVectorIndex


class _FakeEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeClient:
    def __init__(self) -> None:
        self.created: list[str] = []
        self.upserted = []
        self.deleted = []

    async def get_collections(self):
        return SimpleNamespace(collections=[])

    async def create_collection(self, *, collection_name, vectors_config):
        self.created.append(collection_name)

    async def upsert(self, *, collection_name, points):
        self.upserted.extend(points)

    async def delete(self, *, collection_name, points_selector):
        self.deleted.extend(points_selector)

    async def close(self) -> None:
        return None


def _item(item_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title="FAQ",
        layer=KnowledgeLayer.L4_USER_KNOWLEDGE,
        module="demo.channel",
        feature="creation",
        content="published answer",
        status=KnowledgeStatus.PUBLISHED,
        visible_roles=[UserRole.USER],
    )


@pytest.mark.asyncio
async def test_incremental_qdrant_refresh_upserts_and_deletes_by_knowledge_id() -> None:
    index = KnowledgeVectorIndex(collection_name="test_incremental")
    await index._client.close()
    fake = _FakeClient()
    index._client = fake

    item = _item("faq.demo.channel.create.answer")
    result = await index.upsert_items([item], _FakeEmbedder())
    deleted = await index.delete_ids(["faq.demo.channel.create.old"])

    assert result == {"embedded": 1, "upserted": 1}
    assert deleted == 1
    assert fake.created == ["test_incremental"]
    assert len(fake.upserted) == 1
    assert fake.upserted[0].payload["id"] == item.id
    assert fake.upserted[0].payload["status"] == "published"
    assert len(fake.deleted) == 1
