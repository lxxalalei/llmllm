from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.code_index import GoCodeParser, PythonCodeParser, Symbol
from app.knowledge.l1_generator import L1Generator
from app.knowledge.l2_generator import L2Generator


class ScopeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    symbols: list[str] = Field(default_factory=list)


class BatchKnowledgeScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str
    ref: str | None = None
    namespace: str
    module: str
    feature: str
    sources: list[ScopeSource] = Field(min_length=1)


def _parser_for(path: Path):
    if path.suffix == ".go":
        return GoCodeParser()
    if path.suffix == ".py":
        return PythonCodeParser()
    raise ValueError(f"unsupported source language: {path}")


def _select_symbols(parsed: list[Symbol], requested: list[str], path: str) -> list[Symbol]:
    selected = parsed
    if requested:
        requested_set = set(requested)
        selected = [symbol for symbol in parsed if symbol.name in requested_set]
        missing = requested_set - {symbol.name for symbol in selected}
        if missing:
            raise ValueError(
                f"target symbols not found in {path}: {', '.join(sorted(missing))}"
            )

    seen: set[str] = set()
    duplicate_names: set[str] = set()
    for symbol in selected:
        if symbol.name in seen:
            duplicate_names.add(symbol.name)
        seen.add(symbol.name)
    if duplicate_names:
        raise ValueError(
            f"source contains ambiguous same-name symbols in {path}: "
            + ", ".join(sorted(duplicate_names))
        )
    return selected


def _unique_ids(items, *, label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item.id in seen:
            duplicates.add(item.id)
        seen.add(item.id)
    if duplicates:
        raise ValueError(
            f"duplicate knowledge ids across {label}: {', '.join(sorted(duplicates))}"
        )


async def compile_scope_preview(
    *,
    repository_root: str | Path,
    commit: str,
    scope: BatchKnowledgeScope,
    l1_generator: L1Generator,
    l2_generator: L2Generator,
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")

    l1_items = []
    file_reports: list[dict[str, object]] = []
    selected_symbol_count = 0

    for source_target in scope.sources:
        source_path = root / source_target.path
        if not source_path.is_file():
            raise ValueError(f"scope source file not found: {source_target.path}")
        parser = _parser_for(source_path)
        source = source_path.read_text(encoding="utf-8")
        parsed = parser.extract_symbols(source)
        selected = _select_symbols(parsed, source_target.symbols, source_target.path)
        selected_symbol_count += len(selected)

        generated = await l1_generator.generate(
            namespace=scope.namespace,
            module=scope.module,
            feature=scope.feature,
            repo=scope.repo,
            ref=scope.ref,
            commit=commit,
            file=source_target.path,
            symbols=selected,
        )
        l1_items.extend(generated)
        file_reports.append(
            {
                "path": source_target.path,
                "symbols": [symbol.name for symbol in selected],
                "l1_ids": [item.id for item in generated],
            }
        )

    _unique_ids(l1_items, label="compiled L1")
    l2_items = await l2_generator.generate(
        namespace=scope.namespace,
        module=scope.module,
        feature=scope.feature,
        l1_items=l1_items,
        existing_items=[],
    )
    _unique_ids([*l1_items, *l2_items], label="compiled L1/L2")

    return {
        "scope": scope.model_dump(mode="json"),
        "commit": commit,
        "files": file_reports,
        "coverage": {
            "source_files": len(scope.sources),
            "symbols": selected_symbol_count,
            "l1": len(l1_items),
            "l2": len(l2_items),
        },
        "l1_changes": [{"id": item.id, "change": "added"} for item in l1_items],
        "l1_items": [item.model_dump(mode="json") for item in l1_items],
        "l2_changes": [{"id": item.id, "change": "added"} for item in l2_items],
        "l2_items": [item.model_dump(mode="json") for item in l2_items],
        "l3_review": [],
    }
