from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.code_index import GoCodeParser
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus

CHANGED_COMMIT = "43b2ae87e06b06abe01f9382ec26899c54c31728"


@dataclass(frozen=True)
class SymbolChange:
    name: str
    change: str  # added | removed | modified


def symbol_signatures(source: str) -> dict[str, tuple[str, int, int]]:
    """Per-symbol (content hash, start_line, end_line) used to detect drift."""
    symbols = GoCodeParser().extract_symbols(source)
    return {
        symbol.name: (
            hashlib.sha256(symbol.source.encode("utf-8")).hexdigest(),
            symbol.start_line,
            symbol.end_line,
        )
        for symbol in symbols
    }


def changed_symbols(old_source: str, new_source: str) -> list[SymbolChange]:
    """added/removed/modified propagate impact; shifted (line drift with
    identical content) is reported separately and does not propagate."""
    old_sigs = symbol_signatures(old_source)
    new_sigs = symbol_signatures(new_source)
    changes: list[SymbolChange] = []
    for name in sorted(set(old_sigs) | set(new_sigs)):
        if name not in old_sigs:
            changes.append(SymbolChange(name=name, change="added"))
            continue
        if name not in new_sigs:
            changes.append(SymbolChange(name=name, change="removed"))
            continue
        old_content = old_sigs[name][0]
        new_content = new_sigs[name][0]
        if old_content != new_content:
            changes.append(SymbolChange(name=name, change="modified"))
        elif old_sigs[name][1:] != new_sigs[name][1:]:
            changes.append(SymbolChange(name=name, change="shifted"))
    return changes


def bound_l1_items(
    catalog, symbol: str, commit: str | None = None
) -> list[KnowledgeItem]:
    """L1 engineering facts bound to the changed code symbol."""
    result = []
    for item in catalog._items.values():
        if item.layer != KnowledgeLayer.L1_ENGINEERING_FACT:
            continue
        for source in item.sources:
            if source.symbol != symbol:
                continue
            if commit is not None and source.commit != commit:
                continue
            result.append(item)
            break
    return result


def _children_index(catalog) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for item in catalog._items.values():
        for parent_id in item.derived_from:
            children.setdefault(parent_id, []).append(item.id)
    return children


def upstream_items(catalog, root_ids: list[str]) -> list[KnowledgeItem]:
    """All knowledge above the roots, reachable through derived_from edges."""
    children = _children_index(catalog)
    affected: dict[str, KnowledgeItem] = {}
    stack = list(root_ids)
    while stack:
        current_id = stack.pop()
        if current_id in affected:
            continue
        try:
            item = catalog.get(current_id)
        except KeyError:
            continue
        affected[current_id] = item
        stack.extend(children.get(current_id, []))
    return sorted(affected.values(), key=lambda item: item.id)


def propose_state(item: KnowledgeItem) -> KnowledgeStatus | None:
    """Impact propagation rule (roadmap M4 / PRD 15-16).

    L1/L2: content stale until regenerated -> outdated.
    L3:    published product logic must be re-reviewed -> review.
    L4:    published user knowledge may be stale -> outdated.
    Draft/review items are not downgraded; deprecated items stay.
    """
    if item.status == KnowledgeStatus.DEPRECATED:
        return None
    if item.layer in (
        KnowledgeLayer.L1_ENGINEERING_FACT,
        KnowledgeLayer.L2_ENGINEERING_RULE,
    ):
        return KnowledgeStatus.OUTDATED if item.status != KnowledgeStatus.OUTDATED else None
    if item.layer == KnowledgeLayer.L3_PRODUCT_LOGIC:
        if item.status == KnowledgeStatus.PUBLISHED:
            return KnowledgeStatus.REVIEW
        return None
    if item.layer == KnowledgeLayer.L4_USER_KNOWLEDGE:
        return KnowledgeStatus.OUTDATED if item.status == KnowledgeStatus.PUBLISHED else None
    return None


def analyze_impact(
    catalog,
    old_source: str,
    new_source: str,
    commit: str | None = None,
) -> dict[str, object]:
    """Locate changed symbols, bound L1 facts, and the affected upstream set."""
    changes = changed_symbols(old_source, new_source)
    bound: list[KnowledgeItem] = []
    for change in changes:
        if change.change == "shifted":
            continue
        for item in bound_l1_items(catalog, change.name, commit=commit):
            if item not in bound:
                bound.append(item)
    affected = upstream_items(catalog, [item.id for item in bound])
    transitions = []
    for item in affected:
        proposed = propose_state(item)
        if proposed is not None:
            transitions.append(
                {
                    "id": item.id,
                    "layer": item.layer.value,
                    "current": item.status.value,
                    "proposed": proposed.value,
                }
            )
    return {
        "symbol_changes": [{"name": c.name, "change": c.change} for c in changes],
        "bound_l1": [item.id for item in bound],
        "affected": [item.id for item in affected],
        "transitions": transitions,
    }


def apply_transitions(knowledge_root, transitions: list[dict]) -> list[str]:
    """Rewrite frontmatter status lines for each transition. Returns changed files."""
    import re as _re

    by_id = {transition["id"]: transition for transition in transitions}
    changed_files: list[str] = []
    for path in sorted(Path(knowledge_root).rglob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        match = _re.search(r"(?m)^id:\s*(\S+)", text)
        if match is None:
            continue
        transition = by_id.get(match.group(1))
        if transition is None:
            continue
        old_line = f"status: {transition['current']}"
        if old_line not in text:
            raise ValueError(f"cannot find {old_line!r} in {path}")
        path.write_text(text.replace(old_line, f"status: {transition['proposed']}", 1), encoding="utf-8")
        changed_files.append(str(path))
    return changed_files
