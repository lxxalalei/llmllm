from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

from app.code_index import GoCodeParser
from app.core.config import settings
from app.knowledge.l1_generator import L1Generator
from app.llm import OpenAIEngineeringFactExtractor


PINNED_COMMIT = "43b2ae87e06b06abe01f9382ec26899c54c31728"
SOURCE_FILE = Path("server/channels/app/channel.go")
SOURCE_FILE_POSIX = SOURCE_FILE.as_posix()
TARGET_SYMBOLS = {"CreateChannelWithUser", "CreateChannel"}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _validate_checkout(root: Path) -> None:
    head = _git(root, "rev-parse", "HEAD")
    if head != PINNED_COMMIT:
        raise SystemExit(f"Mattermost checkout must be pinned to {PINNED_COMMIT}; got {head}")

    changed = _git(root, "status", "--porcelain", "--", SOURCE_FILE_POSIX)
    if changed:
        raise SystemExit(f"Mattermost source file has local changes: {SOURCE_FILE}")

    if not (root / SOURCE_FILE).is_file():
        raise SystemExit(f"Mattermost source file not found: {root / SOURCE_FILE}")


def _generator() -> L1Generator:
    if settings.llm_provider != "openai":
        raise SystemExit("Set LLM_PROVIDER=openai before running the Mattermost L1 generator")
    if not settings.llm_model:
        raise SystemExit("Set LLM_MODEL before running the Mattermost L1 generator")
    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY before running the Mattermost L1 generator")
    return L1Generator(
        OpenAIEngineeringFactExtractor(
            api_key=settings.llm_api_key, model=settings.llm_model, base_url=settings.llm_base_url
        )
    )


async def _run(root: Path) -> list[dict[str, object]]:
    source = (root / SOURCE_FILE).read_text(encoding="utf-8")
    parsed = GoCodeParser().extract_symbols(source)
    symbols = [symbol for symbol in parsed if symbol.name in TARGET_SYMBOLS]
    found = {symbol.name for symbol in symbols}
    missing = TARGET_SYMBOLS - found
    if missing:
        raise SystemExit(f"target Mattermost symbols not found: {', '.join(sorted(missing))}")

    generator = _generator()
    try:
        items = await generator.generate(
            namespace="mattermost.channel.create",
            module="mattermost.channel",
            feature="channel_creation",
            repo="mattermost/mattermost",
            ref="master",
            commit=PINNED_COMMIT,
            file=SOURCE_FILE_POSIX,
            symbols=symbols,
        )
    finally:
        await generator.close()
    return [item.model_dump(mode="json") for item in items]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Mattermost Channel Creation L1 draft facts")
    parser.add_argument("mattermost_root", type=Path, help="Path to a local mattermost/mattermost checkout")
    parser.add_argument("--output", type=Path, help="Optional JSON output path; stdout is used by default")
    args = parser.parse_args()

    root = args.mattermost_root.resolve()
    _validate_checkout(root)
    payload = asyncio.run(_run(root))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
