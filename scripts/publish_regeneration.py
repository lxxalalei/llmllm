from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.core.config import settings
from app.knowledge import KnowledgeCatalog
from app.knowledge.embeddings import OpenAIEmbeddingProvider
from app.knowledge.publish import apply_publish_plan, plan_regeneration_publish
from app.knowledge.vector_index import KnowledgeVectorIndex


async def _sync_index(
    *,
    knowledge_root: Path,
    upsert_ids: list[str],
    delete_ids: list[str],
) -> dict[str, int]:
    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY before incremental Qdrant sync")
    if not settings.embedding_model:
        raise SystemExit("Set EMBEDDING_MODEL before incremental Qdrant sync")

    catalog = KnowledgeCatalog.from_directory(knowledge_root)
    items = [catalog.get(knowledge_id) for knowledge_id in upsert_ids]
    embedder = OpenAIEmbeddingProvider(
        api_key=settings.llm_api_key,
        model=settings.embedding_model,
        base_url=settings.llm_base_url,
    )
    index = KnowledgeVectorIndex()
    try:
        if not await index.is_available():
            raise SystemExit(f"Qdrant unavailable at {settings.qdrant_url}")
        upserted = await index.upsert_items(items, embedder)
        deleted = await index.delete_ids(delete_ids)
        return {
            "embedded": upserted["embedded"],
            "upserted": upserted["upserted"],
            "deleted": deleted,
        }
    finally:
        await embedder.close()
        await index.close()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review/publish a Phase 3 regeneration preview into canonical Markdown"
    )
    parser.add_argument("preview", type=Path, help="M2 regeneration preview JSON")
    parser.add_argument("--knowledge-root", type=Path, default=Path("knowledge"))
    parser.add_argument(
        "--approve",
        action="store_true",
        help="apply the publish plan; without this flag the command is dry-run only",
    )
    parser.add_argument(
        "--sync-qdrant",
        action="store_true",
        help="after approved Markdown write, incrementally refresh affected Qdrant points",
    )
    args = parser.parse_args()

    if args.sync_qdrant and not args.approve:
        raise SystemExit("--sync-qdrant requires --approve")

    preview = json.loads(args.preview.read_text(encoding="utf-8"))
    if not isinstance(preview, dict):
        raise SystemExit("preview JSON must be an object")

    plan = plan_regeneration_publish(preview, knowledge_root=args.knowledge_root)
    plan_payload = {
        "writes": [str(write.path) for write in plan.writes],
        "deletes": [str(path) for path in plan.deletes],
        "index_upsert_ids": list(plan.index_upsert_ids),
        "index_delete_ids": list(plan.index_delete_ids),
        "approved": args.approve,
    }
    print(json.dumps(plan_payload, ensure_ascii=False, indent=2))

    if not args.approve:
        return

    result = apply_publish_plan(plan)
    print(json.dumps({"publish": result}, ensure_ascii=False, indent=2))

    if args.sync_qdrant:
        sync = await _sync_index(
            knowledge_root=args.knowledge_root,
            upsert_ids=list(plan.index_upsert_ids),
            delete_ids=list(plan.index_delete_ids),
        )
        print(json.dumps({"qdrant": sync}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
