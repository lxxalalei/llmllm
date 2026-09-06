from __future__ import annotations

from pathlib import Path

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.code_index import GoCodeParser, PythonCodeParser, Symbol
from app.knowledge.l1_generator import L1Generator
from app.knowledge.l2_generator import L2Generator
from app.knowledge.upper_generator import L3Generator, L4Generator


L1_SYMBOLS_PER_REQUEST = 4


class ScopeRange(BaseModel):
    """A bounded excerpt inside a real top-level source symbol."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_line_order(self) -> ScopeRange:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ScopeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    symbols: list[str] = Field(default_factory=list)
    ranges: list[ScopeRange] = Field(default_factory=list)


class BatchKnowledgeScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str
    ref: str | None = None
    namespace: str
    module: str
    feature: str
    propagation: Literal["review", "auto_publish"] = "review"
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


def _select_ranges(
    source: str,
    parsed: list[Symbol],
    requested: list[ScopeRange],
    path: str,
) -> list[Symbol]:
    lines = source.splitlines()
    selected: list[Symbol] = []
    for target in requested:
        matches = [symbol for symbol in parsed if symbol.name == target.symbol]
        if len(matches) != 1:
            raise ValueError(
                f"source range symbol must resolve exactly once in {path}: {target.symbol}"
            )
        container = matches[0]
        if target.start_line < container.start_line or target.end_line > container.end_line:
            raise ValueError(
                f"source range must stay within {target.symbol} in {path}: "
                f"{target.start_line}-{target.end_line}"
            )
        selected.append(
            Symbol(
                kind=container.kind,
                name=container.name,
                start_line=target.start_line,
                end_line=target.end_line,
                source="\n".join(lines[target.start_line - 1 : target.end_line]),
            )
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


def _chunks(items: list[Symbol], size: int) -> list[list[Symbol]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


async def compile_scope_preview(
    *,
    repository_root: str | Path,
    commit: str,
    scope: BatchKnowledgeScope,
    l1_generator: L1Generator,
    l2_generator: L2Generator,
    l3_generator: L3Generator | None = None,
    l4_generator: L4Generator | None = None,
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
        if source_target.ranges and not source_target.symbols:
            selected_symbols = []
        else:
            selected_symbols = _select_symbols(
                parsed, source_target.symbols, source_target.path
            )
        selected_ranges = _select_ranges(
            source, parsed, source_target.ranges, source_target.path
        )
        selected = [*selected_symbols, *selected_ranges]
        duplicate_targets = {
            symbol.name
            for symbol in selected
            if sum(item.name == symbol.name for item in selected) > 1
        }
        if duplicate_targets:
            raise ValueError(
                f"scope selects the same symbol more than once in {source_target.path}: "
                + ", ".join(sorted(duplicate_targets))
            )
        selected_symbol_count += len(selected)

        generated = []
        symbol_batches = _chunks(selected_symbols, L1_SYMBOLS_PER_REQUEST)
        range_batches = [[item] for item in selected_ranges]
        for symbol_batch in [*symbol_batches, *range_batches]:
            generated.extend(
                await l1_generator.generate(
                    namespace=scope.namespace,
                    module=scope.module,
                    feature=scope.feature,
                    repo=scope.repo,
                    ref=scope.ref,
                    commit=commit,
                    file=source_target.path,
                    symbols=symbol_batch,
                )
            )
        l1_items.extend(generated)
        file_reports.append(
            {
                "path": source_target.path,
                "symbols": [symbol.name for symbol in selected],
                "ranges": [item.model_dump(mode="json") for item in source_target.ranges],
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

    l3_items = []
    l4_items = []
    if scope.propagation == "auto_publish":
        if l3_generator is None or l4_generator is None:
            raise ValueError("auto_publish scope requires L3 and L4 generators")
        l3_items = await l3_generator.generate(
            namespace=scope.namespace,
            module=scope.module,
            feature=scope.feature,
            l2_items=l2_items,
        )
        l4_items = await l4_generator.generate(
            namespace=scope.namespace,
            module=scope.module,
            feature=scope.feature,
            l3_items=l3_items,
        )
        _unique_ids([*l1_items, *l2_items, *l3_items, *l4_items], label="compiled knowledge")

    return {
        "scope": scope.model_dump(mode="json"),
        "commit": commit,
        "files": file_reports,
        "coverage": {
            "source_files": len(scope.sources),
            "symbols": selected_symbol_count,
            "l1": len(l1_items),
            "l2": len(l2_items),
            **(
                {"l3": len(l3_items), "l4": len(l4_items)}
                if scope.propagation == "auto_publish"
                else {}
            ),
        },
        "l1_changes": [{"id": item.id, "change": "added"} for item in l1_items],
        "l1_items": [item.model_dump(mode="json") for item in l1_items],
        "l2_changes": [{"id": item.id, "change": "added"} for item in l2_items],
        "l2_items": [item.model_dump(mode="json") for item in l2_items],
        "l3_changes": [{"id": item.id, "change": "added"} for item in l3_items],
        "l3_items": [item.model_dump(mode="json") for item in l3_items],
        "l4_changes": [{"id": item.id, "change": "added"} for item in l4_items],
        "l4_items": [item.model_dump(mode="json") for item in l4_items],
        "l3_review": [],
    }
