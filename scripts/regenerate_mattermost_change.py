from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.core.config import settings
from app.integrations.github import GitHubChangedFile, GitHubSourceClient, bound_source_baselines
from app.knowledge import KnowledgeCatalog
from app.knowledge.l1_generator import L1Generator
from app.knowledge.l2_generator import L2Generator
from app.knowledge.regeneration import regenerate_go_file
from app.llm import OpenAIEngineeringFactExtractor, OpenAIEngineeringRuleExtractor


REPOSITORY = "mattermost/mattermost"
PUSH_REF = "refs/heads/master"
SOURCE_FILE = "server/channels/app/channel.go"
KNOWLEDGE_ROOT = Path("knowledge")


def _configured_generators() -> tuple[L1Generator, L2Generator]:
    if settings.llm_provider != "openai":
        raise SystemExit("Set LLM_PROVIDER=openai before running incremental regeneration")
    if not settings.llm_model:
        raise SystemExit("Set LLM_MODEL before running incremental regeneration")
    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY before running incremental regeneration")

    l1 = L1Generator(
        OpenAIEngineeringFactExtractor(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )
    )
    l2 = L2Generator(
        OpenAIEngineeringRuleExtractor(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )
    )
    return l1, l2


def _target_change(changed: list[GitHubChangedFile]) -> GitHubChangedFile | None:
    matches = [
        item
        for item in changed
        if item.path == SOURCE_FILE or item.previous_path == SOURCE_FILE
    ]
    if len(matches) > 1:
        raise ValueError(f"multiple compare entries matched tracked source: {SOURCE_FILE}")
    return matches[0] if matches else None


async def _run(after: str) -> dict[str, object]:
    catalog = KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)
    baselines = bound_source_baselines(catalog, REPOSITORY, PUSH_REF)
    baseline = baselines.get(SOURCE_FILE)
    if baseline is None:
        raise SystemExit(f"no L1 SourceBinding baseline for {REPOSITORY}:{SOURCE_FILE}")
    if after == baseline:
        return {
            "repository": REPOSITORY,
            "baseline": baseline,
            "after": after,
            "source_file": SOURCE_FILE,
            "changed": False,
            "reason": "target commit equals current knowledge baseline",
        }

    client = GitHubSourceClient(token=settings.github_token)
    try:
        changed = await client.compare_files(REPOSITORY, baseline, after)
        target = _target_change(changed)
        if target is None:
            return {
                "repository": REPOSITORY,
                "baseline": baseline,
                "after": after,
                "source_file": SOURCE_FILE,
                "changed": False,
                "reason": "tracked source file is unchanged in compare range",
            }

        old_file = target.previous_path or SOURCE_FILE
        new_file = target.path
        old_source = ""
        new_source = ""

        if target.status != "added":
            fetched_old = await client.fetch_text(REPOSITORY, baseline, old_file)
            if fetched_old is None:
                raise ValueError(f"cannot read old source {REPOSITORY}@{baseline}:{old_file}")
            old_source = fetched_old
        if target.status != "removed":
            fetched_new = await client.fetch_text(REPOSITORY, after, new_file)
            if fetched_new is None:
                raise ValueError(f"cannot read new source {REPOSITORY}@{after}:{new_file}")
            new_source = fetched_new
    finally:
        await client.close()

    l1_generator, l2_generator = _configured_generators()
    try:
        report = await regenerate_go_file(
            catalog=catalog,
            repo=REPOSITORY,
            baseline=baseline,
            after=after,
            old_file=old_file,
            new_file=new_file,
            old_source=old_source,
            new_source=new_source,
            l1_generator=l1_generator,
            l2_generator=l2_generator,
        )
    finally:
        await l1_generator.close()
        await l2_generator.close()

    return {
        "repository": REPOSITORY,
        "baseline": baseline,
        "after": after,
        "source_file": SOURCE_FILE,
        "changed": True,
        "file_status": target.status,
        **report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run Mattermost Channel Creation incremental knowledge regeneration"
    )
    parser.add_argument("after", help="Mattermost target commit SHA")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    if len(args.after) != 40 or any(ch not in "0123456789abcdef" for ch in args.after):
        raise SystemExit("after must be a 40-character lowercase hexadecimal commit SHA")

    payload = asyncio.run(_run(args.after))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
