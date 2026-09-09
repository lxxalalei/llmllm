"""Generate an L4 preview; canonical assets are never written by this command."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import yaml

from app.core.config import settings
from app.knowledge.assets import KnowledgeCatalog
from app.knowledge.behavior_rules import BehaviorRule
from app.knowledge.l4_compiler import L4IntentManifest, compile_l4_preview, validate_l4_inputs


def validate_output_path(output: Path | None, roots: list[Path], inputs: list[Path]) -> None:
    if output is None:
        return
    target = output.resolve()
    if any(target == root.resolve() or root.resolve() in target.parents for root in roots):
        raise ValueError("preview output must be outside canonical knowledge/rule roots")
    if target in {path.resolve() for path in inputs}:
        raise ValueError("preview output cannot overwrite an input")
    if target.suffix.lower() != ".json":
        raise ValueError("preview output must be JSON")


async def _run(manifest: L4IntentManifest, catalog: KnowledgeCatalog, rules: list[BehaviorRule]):
    from app.llm.l4_provider import OpenAIL4Composer

    if settings.llm_provider != "openai" or not settings.llm_model or not settings.llm_api_key:
        raise ValueError("Set LLM_PROVIDER=openai, LLM_MODEL and LLM_API_KEY before generating L4")
    composer = OpenAIL4Composer(api_key=settings.llm_api_key, model=settings.llm_model, base_url=settings.llm_base_url, reasoning_effort=settings.llm_reasoning_effort)
    try:
        return await compile_l4_preview(manifest=manifest, catalog=catalog, rules=rules, composer=composer)
    finally:
        await composer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan, write and review L4 user-intent drafts without publishing")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--knowledge-root", type=Path, default=Path("knowledge"))
    parser.add_argument("--rule-root", type=Path, help="Defaults to KNOWLEDGE_ROOT/behavior-rules")
    parser.add_argument("--output", type=Path, help="Preview JSON outside canonical roots; defaults to stdout")
    args = parser.parse_args()
    rule_root = args.rule_root or args.knowledge_root / "behavior-rules"
    try:
        validate_output_path(args.output, [args.knowledge_root, rule_root], [args.manifest])
        if not args.knowledge_root.is_dir() or not rule_root.is_dir():
            raise ValueError("knowledge and rule roots must be existing directories")
        manifest = L4IntentManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
        catalog = KnowledgeCatalog.from_directory(args.knowledge_root)
        rules = [BehaviorRule.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))) for path in sorted(rule_root.rglob("*.yaml"))]
        validate_l4_inputs(manifest=manifest, catalog=catalog, rules=rules)
        preview = asyncio.run(_run(manifest, catalog, rules))
        payload = preview.model_dump_json(indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
