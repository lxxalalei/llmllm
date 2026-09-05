from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.code_index import GoCodeParser, Symbol
from app.knowledge.impact import changed_symbols, upstream_items
from app.knowledge.models import (
    KnowledgeItem,
    KnowledgeLayer,
    KnowledgeStatus,
    SourceBinding,
)


ChangeKind = Literal["unchanged", "changed", "added", "removed"]


@dataclass(frozen=True)
class KnowledgeChange:
    id: str
    change: ChangeKind
    before: KnowledgeItem | None
    after: KnowledgeItem | None


@dataclass(frozen=True)
class FileKnowledgeScope:
    namespace: str
    module: str
    feature: str
    ref: str | None


def _statement(item: KnowledgeItem) -> str:
    lines = item.content.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def _semantic_signature(item: KnowledgeItem) -> tuple[object, ...]:
    signature: list[object] = [item.title.strip(), _statement(item)]
    if item.layer == KnowledgeLayer.L2_ENGINEERING_RULE:
        signature.append(tuple(item.derived_from))
    return tuple(signature)


def _by_unique_id(
    items: list[KnowledgeItem],
    *,
    label: str,
) -> dict[str, KnowledgeItem]:
    result: dict[str, KnowledgeItem] = {}
    for item in items:
        if item.id in result:
            raise ValueError(f"duplicate knowledge id in {label}: {item.id}")
        result[item.id] = item
    return result


def diff_items(
    before: list[KnowledgeItem],
    after: list[KnowledgeItem],
) -> list[KnowledgeChange]:
    before_by_id = _by_unique_id(before, label="before set")
    after_by_id = _by_unique_id(after, label="after set")
    changes: list[KnowledgeChange] = []
    for knowledge_id in sorted(set(before_by_id) | set(after_by_id)):
        old = before_by_id.get(knowledge_id)
        new = after_by_id.get(knowledge_id)
        if old is None:
            kind: ChangeKind = "added"
        elif new is None:
            kind = "removed"
        elif _semantic_signature(old) == _semantic_signature(new):
            kind = "unchanged"
        else:
            kind = "changed"
        changes.append(KnowledgeChange(knowledge_id, kind, old, new))
    return changes


def diff_l1(
    before: list[KnowledgeItem],
    after: list[KnowledgeItem],
) -> list[KnowledgeChange]:
    return diff_items(before, after)


def _namespace_from_id(knowledge_id: str) -> str:
    prefix, separator, _key = knowledge_id.rpartition(".")
    if not separator or not prefix.startswith("eng."):
        raise ValueError(f"cannot infer engineering namespace from knowledge id: {knowledge_id}")
    return prefix.removeprefix("eng.")


def file_l1_items(
    catalog,
    *,
    repo: str,
    file: str,
    commit: str,
) -> list[KnowledgeItem]:
    items: list[KnowledgeItem] = []
    for item in catalog._items.values():
        if item.layer != KnowledgeLayer.L1_ENGINEERING_FACT:
            continue
        if any(
            source.repo == repo and source.file == file and source.commit == commit
            for source in item.sources
        ):
            items.append(item)
    return sorted(items, key=lambda item: item.id)


def infer_file_scope(items: list[KnowledgeItem]) -> FileKnowledgeScope:
    if not items:
        raise ValueError("cannot infer knowledge scope without bound L1 items")
    modules = {item.module for item in items}
    features = {item.feature for item in items}
    namespaces = {_namespace_from_id(item.id) for item in items}
    refs = {
        source.ref
        for item in items
        for source in item.sources
        if source.ref is not None
    }
    if len(modules) != 1 or len(features) != 1 or len(namespaces) != 1:
        raise ValueError("automatic regeneration currently requires one knowledge scope per source file")
    if len(refs) > 1:
        raise ValueError("automatic regeneration currently requires one source ref per source file")
    feature = next(iter(features))
    if feature is None:
        raise ValueError("automatic regeneration requires a feature on bound L1 items")
    return FileKnowledgeScope(
        namespace=next(iter(namespaces)),
        module=next(iter(modules)),
        feature=feature,
        ref=next(iter(refs)) if refs else None,
    )


def _matching_source(
    item: KnowledgeItem,
    *,
    repo: str,
    file: str,
    commit: str,
) -> SourceBinding:
    for source in item.sources:
        if source.repo == repo and source.file == file and source.commit == commit:
            return source
    raise ValueError(f"knowledge item is not bound to {repo}@{commit}:{file}: {item.id}")


def _carry_forward(
    item: KnowledgeItem,
    *,
    old_file: str,
    new_file: str,
    repo: str,
    baseline: str,
    after: str,
    symbol: Symbol,
) -> KnowledgeItem:
    sources: list[SourceBinding] = []
    for source in item.sources:
        if source.repo == repo and source.file == old_file and source.commit == baseline:
            sources.append(
                source.model_copy(
                    update={
                        "commit": after,
                        "file": new_file,
                        "start_line": symbol.start_line,
                        "end_line": symbol.end_line,
                    }
                )
            )
        else:
            sources.append(source)
    return item.model_copy(update={"sources": sources})


def _version_generated(
    generated: list[KnowledgeItem],
    existing: list[KnowledgeItem],
) -> list[KnowledgeItem]:
    existing_by_id = {item.id: item for item in existing}
    result: list[KnowledgeItem] = []
    for item in generated:
        old = existing_by_id.get(item.id)
        if old is None:
            result.append(item)
            continue
        updates: dict[str, object] = {
            "version": old.version,
            "created_at": old.created_at,
        }
        if _semantic_signature(old) == _semantic_signature(item):
            updates["status"] = old.status
        else:
            updates["version"] = old.version + 1
        result.append(item.model_copy(update=updates))
    return result


def _feature_l1(catalog, *, module: str, feature: str) -> list[KnowledgeItem]:
    return sorted(
        [
            item
            for item in catalog._items.values()
            if item.layer == KnowledgeLayer.L1_ENGINEERING_FACT
            and item.module == module
            and item.feature == feature
        ],
        key=lambda item: item.id,
    )


def _feature_l2(catalog, *, module: str, feature: str) -> list[KnowledgeItem]:
    return sorted(
        [
            item
            for item in catalog._items.values()
            if item.layer == KnowledgeLayer.L2_ENGINEERING_RULE
            and item.module == module
            and item.feature == feature
        ],
        key=lambda item: item.id,
    )


def _replace_file_l1(
    catalog,
    *,
    module: str,
    feature: str,
    old_file_items: list[KnowledgeItem],
    new_file_items: list[KnowledgeItem],
) -> list[KnowledgeItem]:
    replaced_ids = {item.id for item in old_file_items}
    current = [
        item
        for item in _feature_l1(catalog, module=module, feature=feature)
        if item.id not in replaced_ids
    ]
    current.extend(new_file_items)
    return sorted(current, key=lambda item: item.id)


async def regenerate_go_file_l1(
    *,
    catalog,
    repo: str,
    baseline: str,
    after: str,
    old_file: str,
    new_file: str,
    old_source: str,
    new_source: str,
    l1_generator,
) -> dict[str, object]:
    """Regenerate changed Go symbols while advancing all surviving file bindings.

    Only added/removed/modified symbols are sent to the model. Facts on
    untouched or line-shifted symbols are carried forward and rebound to the
    new commit so a source file keeps one authoritative baseline.
    """
    existing = file_l1_items(catalog, repo=repo, file=old_file, commit=baseline)
    scope = infer_file_scope(existing)
    symbol_changes = changed_symbols(old_source, new_source)
    semantic_names = {
        change.name for change in symbol_changes if change.change != "shifted"
    }

    parsed_new = GoCodeParser().extract_symbols(new_source)
    new_symbol_map = {symbol.name: symbol for symbol in parsed_new}
    old_changed = [
        item
        for item in existing
        if _matching_source(item, repo=repo, file=old_file, commit=baseline).symbol
        in semantic_names
    ]
    regenerate_symbols = [
        symbol for name, symbol in new_symbol_map.items() if name in semantic_names
    ]

    generated: list[KnowledgeItem] = []
    if regenerate_symbols:
        generated = await l1_generator.generate(
            namespace=scope.namespace,
            module=scope.module,
            feature=scope.feature,
            repo=repo,
            ref=scope.ref,
            commit=after,
            file=new_file,
            symbols=regenerate_symbols,
            existing_items=old_changed,
        )
        generated = _version_generated(generated, old_changed)

    carried: list[KnowledgeItem] = []
    for item in existing:
        source = _matching_source(item, repo=repo, file=old_file, commit=baseline)
        if source.symbol is None:
            raise ValueError(f"L1 source binding has no symbol: {item.id}")
        if source.symbol in semantic_names:
            continue
        symbol = new_symbol_map.get(source.symbol)
        if symbol is None:
            raise ValueError(
                f"bound symbol missing from new source without a detected removal: {source.symbol}"
            )
        carried.append(
            _carry_forward(
                item,
                old_file=old_file,
                new_file=new_file,
                repo=repo,
                baseline=baseline,
                after=after,
                symbol=symbol,
            )
        )

    new_items = sorted([*carried, *generated], key=lambda item: item.id)
    changes = diff_items(existing, new_items)
    return {
        "repo": repo,
        "baseline": baseline,
        "after": after,
        "old_file": old_file,
        "new_file": new_file,
        "scope": {
            "namespace": scope.namespace,
            "module": scope.module,
            "feature": scope.feature,
            "ref": scope.ref,
        },
        "symbol_changes": [
            {"name": change.name, "change": change.change}
            for change in symbol_changes
        ],
        "l1_changes": [
            {"id": change.id, "change": change.change}
            for change in changes
        ],
        "l1_items": [item.model_dump(mode="json") for item in new_items],
    }


async def regenerate_go_file(
    *,
    catalog,
    repo: str,
    baseline: str,
    after: str,
    old_file: str,
    new_file: str,
    old_source: str,
    new_source: str,
    l1_generator,
    l2_generator,
) -> dict[str, object]:
    """Run Phase 3 M2 for one changed Go file through L2 and L3 review routing."""
    report = await regenerate_go_file_l1(
        catalog=catalog,
        repo=repo,
        baseline=baseline,
        after=after,
        old_file=old_file,
        new_file=new_file,
        old_source=old_source,
        new_source=new_source,
        l1_generator=l1_generator,
    )
    scope = report["scope"]
    new_file_l1 = [
        KnowledgeItem.model_validate(item) for item in report["l1_items"]
    ]
    old_file_l1 = file_l1_items(
        catalog, repo=repo, file=old_file, commit=baseline
    )
    current_l1 = _replace_file_l1(
        catalog,
        module=scope["module"],
        feature=scope["feature"],
        old_file_items=old_file_l1,
        new_file_items=new_file_l1,
    )
    existing_l2 = _feature_l2(
        catalog, module=scope["module"], feature=scope["feature"]
    )

    l1_semantic_change = any(
        item["change"] != "unchanged" for item in report["l1_changes"]
    )
    if l1_semantic_change:
        generated_l2 = await l2_generator.generate(
            namespace=scope["namespace"],
            module=scope["module"],
            feature=scope["feature"],
            l1_items=current_l1,
            existing_items=existing_l2,
        )
        generated_l2 = _version_generated(generated_l2, existing_l2)
    else:
        generated_l2 = existing_l2

    l2_changes = diff_items(existing_l2, generated_l2)
    changed_l2_ids = [
        change.id for change in l2_changes if change.change != "unchanged"
    ]
    l3_review = [
        item.id
        for item in upstream_items(catalog, changed_l2_ids)
        if item.layer == KnowledgeLayer.L3_PRODUCT_LOGIC
        and item.status != KnowledgeStatus.DEPRECATED
    ]

    return {
        **report,
        "l2_changes": [
            {"id": change.id, "change": change.change}
            for change in l2_changes
        ],
        "l2_items": [item.model_dump(mode="json") for item in generated_l2],
        "l3_review": sorted(set(l3_review)),
    }
