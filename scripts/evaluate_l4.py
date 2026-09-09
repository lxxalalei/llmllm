from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.knowledge import KnowledgeCatalog
from app.knowledge.l4_compiler import L4Preview
from app.knowledge.l4_evaluation import (
    L4EvaluationDataset,
    evaluate_l4_preview,
    validate_evaluation_cases,
)
from app.knowledge.qa import OpenAIQAResponder


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc.msg}") from exc


def validate_output_path(output: Path | None, roots: list[Path], inputs: list[Path]) -> None:
    """Keep a report from overwriting canonical assets or its input files."""

    if output is None:
        return
    target = output.resolve()
    resolved_roots = [root.resolve() for root in roots]
    if any(target == root or root in target.parents for root in resolved_roots):
        raise ValueError("evaluation output must be outside the canonical knowledge root")
    if target in {path.resolve() for path in inputs}:
        raise ValueError("evaluation output cannot overwrite an input")
    if target.suffix.lower() != ".json":
        raise ValueError("evaluation output must be JSON")


def _parse_inputs(preview_path: Path, dataset_path: Path) -> tuple[L4Preview, L4EvaluationDataset]:
    # Validate the raw JSON into typed compiler/dataset objects before any
    # optional model client is constructed.
    try:
        preview = L4Preview.model_validate(_read_json(preview_path))
    except ValidationError as exc:
        raise ValueError(f"invalid L4 preview: {exc}") from exc
    try:
        dataset = L4EvaluationDataset.model_validate(_read_json(dataset_path))
    except ValidationError as exc:
        raise ValueError(f"invalid evaluation dataset: {exc}") from exc
    if (dataset.module, dataset.feature) != (preview.module, preview.feature):
        raise ValueError(
            "preview and dataset module/feature do not match: "
            f"preview={preview.module}/{preview.feature}, "
            f"dataset={dataset.module}/{dataset.feature}"
        )
    validate_evaluation_cases(preview, dataset.cases)
    return preview, dataset


def _report_has_failure(report: dict[str, Any], *, with_llm: bool) -> bool:
    candidate_failed = report.get("candidates", {}).get("rejected_count", 0) > 0
    retrieval_failed = any(
        case["retrieval_evaluable"] and not case["retrieval_pass"]
        for case in report["cases"]
    )
    qa_failed = with_llm and any(
        case["qa_evaluable"] and not case.get("qa_pass", False)
        for case in report["cases"]
    )
    return candidate_failed or retrieval_failed or qa_failed


async def _run(args: argparse.Namespace) -> int:
    validate_output_path(args.output, [args.knowledge_root], [args.preview, args.dataset])
    preview, dataset = _parse_inputs(args.preview, args.dataset)
    catalog = KnowledgeCatalog.from_directory(args.knowledge_root)

    responder = None
    if args.with_llm:
        if settings.llm_provider != "openai" or not settings.llm_api_key or not settings.llm_model:
            raise ValueError(
                "--with-llm requires LLM_PROVIDER=openai, LLM_API_KEY and LLM_MODEL"
            )
        responder = OpenAIQAResponder(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            reasoning_effort=settings.llm_reasoning_effort,
        )

    try:
        report = await evaluate_l4_preview(
            catalog,
            preview,
            dataset.cases,
            responder=responder,
        )
    finally:
        if responder is not None:
            await responder.close()

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    return 1 if _report_has_failure(report, with_llm=args.with_llm) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate an L4 preview in an in-memory simulated serve catalog; "
            "this command never publishes canonical knowledge"
        )
    )
    parser.add_argument("preview", type=Path, help="typed L4 preview JSON")
    parser.add_argument("dataset", type=Path, help="typed L4 evaluation dataset JSON")
    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=Path("knowledge"),
        help="canonical knowledge directory to read (default: knowledge)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional report JSON path; omitted reports to stdout",
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="run local retrieval plus configured OpenAI-compatible QA; requires model settings",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except (OSError, ValueError) as exc:
        print(f"evaluate_l4: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
