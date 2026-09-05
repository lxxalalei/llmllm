from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

from app.core.config import settings
from app.knowledge import KnowledgeCatalog, KnowledgeLayer
from app.knowledge.batch_compiler import BatchKnowledgeScope, compile_scope_preview
from app.knowledge.l1_generator import L1Generator
from app.knowledge.l2_generator import L2Generator
from app.llm import OpenAIEngineeringFactExtractor, OpenAIEngineeringRuleExtractor


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _generators() -> tuple[L1Generator, L2Generator]:
    if settings.llm_provider != "openai":
        raise SystemExit("Set LLM_PROVIDER=openai before compiling a knowledge scope")
    if not settings.llm_model:
        raise SystemExit("Set LLM_MODEL before compiling a knowledge scope")
    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY before compiling a knowledge scope")
    kwargs = {
        "api_key": settings.llm_api_key,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
    }
    return (
        L1Generator(OpenAIEngineeringFactExtractor(**kwargs)),
        L2Generator(OpenAIEngineeringRuleExtractor(**kwargs)),
    )


def _assert_new_feature(scope: BatchKnowledgeScope, knowledge_root: Path) -> None:
    catalog = KnowledgeCatalog.from_directory(knowledge_root)
    existing = [
        item.id
        for item in catalog._items.values()
        if item.module == scope.module
        and item.feature == scope.feature
        and item.layer
        in {KnowledgeLayer.L1_ENGINEERING_FACT, KnowledgeLayer.L2_ENGINEERING_RULE}
    ]
    if existing:
        raise SystemExit(
            "batch compiler currently creates new feature knowledge only; "
            f"existing feature knowledge found: {', '.join(sorted(existing))}"
        )


async def _run(
    repository_root: Path,
    scope: BatchKnowledgeScope,
    commit: str,
) -> dict[str, object]:
    l1_generator, l2_generator = _generators()
    try:
        return await compile_scope_preview(
            repository_root=repository_root,
            commit=commit,
            scope=scope,
            l1_generator=l1_generator,
            l2_generator=l2_generator,
        )
    finally:
        await l1_generator.close()
        await l2_generator.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile one repository feature scope into L1/L2 knowledge preview"
    )
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("scope", type=Path, help="JSON BatchKnowledgeScope file")
    parser.add_argument("--knowledge-root", type=Path, default=Path("knowledge"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repository_root = args.repository_root.resolve()
    scope = BatchKnowledgeScope.model_validate_json(args.scope.read_text(encoding="utf-8"))
    _assert_new_feature(scope, args.knowledge_root)
    commit = _git(repository_root, "rev-parse", "HEAD")

    payload = asyncio.run(_run(repository_root, scope, commit))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
