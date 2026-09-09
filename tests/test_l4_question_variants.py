from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.knowledge.assets import KnowledgeCatalog, load_knowledge_file
from app.knowledge.models import KnowledgeItem, UserRole
from app.knowledge.publish import render_knowledge_item
from app.knowledge.retrieval import retrieve
from app.knowledge.vector_index import KnowledgeVectorIndex


def item():
    return KnowledgeItem(id="faq.example", title="Creation permissions", layer="L4", module="example", content="The matching creation permission is required.", status="published", visible_roles=["user"], question_variants=["Why is the blue banana button disabled?"])


def test_question_variants_survive_markdown_and_retrieve_same_faq(tmp_path):
    path = tmp_path / "faq.md"
    path.write_text(render_knowledge_item(item()), encoding="utf-8")
    restored = load_knowledge_file(path)
    assert restored.question_variants == item().question_variants
    hits = retrieve(KnowledgeCatalog([restored]), "blue banana button", UserRole.USER)
    assert hits and hits[0].item.id == restored.id


@pytest.mark.asyncio
async def test_embedding_input_contains_synonymous_questions():
    index = KnowledgeVectorIndex.__new__(KnowledgeVectorIndex)
    index._collection = "test"
    index._client = SimpleNamespace(upsert=AsyncMock())
    index.ensure_collection = AsyncMock()
    embedder = SimpleNamespace(embed=AsyncMock(return_value=[[1.0, 0.0]]))
    assert await index.upsert_items([item()], embedder) == {"embedded": 1, "upserted": 1}
    assert "blue banana button" in embedder.embed.call_args.args[0][0]
