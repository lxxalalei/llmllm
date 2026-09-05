from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.core.config import settings
from app.knowledge import KnowledgeCatalog
from app.knowledge.embeddings import OpenAIEmbeddingProvider
from app.knowledge.vector_index import COLLECTION, KnowledgeVectorIndex

KNOWLEDGE_ROOT = Path("knowledge")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Full re-sync of knowledge/ assets into the Qdrant index"
    )
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_ROOT)
    parser.add_argument("--model", default=settings.embedding_model,
                        help="embedding model id (default: EMBEDDING_MODEL env / settings)")
    parser.add_argument("--collection", default=None)
    args = parser.parse_args()

    if args.collection is not None:
        raise SystemExit("--collection is reserved; use app.knowledge.vector_index.COLLECTION")

    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY before syncing the Qdrant index")
    if not args.model:
        raise SystemExit("Set EMBEDDING_MODEL (e.g. GLM/Embedding-3) before syncing")

    catalog = KnowledgeCatalog.from_directory(args.knowledge_root)
    items = sorted(catalog._items.values(), key=lambda item: item.id)
    embedder = OpenAIEmbeddingProvider(api_key=settings.llm_api_key, model=args.model)
    index = KnowledgeVectorIndex()
    try:
        if not await index.is_available():
            raise SystemExit(f"Qdrant unavailable at {settings.qdrant_url}")
        result = await index.replace_all(items, embedder)
        print(f"synced items={result['embedded']} upserted={result['upserted']} "
              f"deleted={result['deleted']} collection={COLLECTION}")
    finally:
        await embedder.close()
        await index.close()


if __name__ == "__main__":
    asyncio.run(main())
