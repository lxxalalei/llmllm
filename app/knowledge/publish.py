from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.knowledge.assets import KnowledgeCatalog, load_knowledge_file
from app.knowledge.impact import upstream_items
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus


_LAYER_DIRS = {
    KnowledgeLayer.L1_ENGINEERING_FACT: "l1-engineering-facts",
    KnowledgeLayer.L2_ENGINEERING_RULE: "l2-engineering-rules",
    KnowledgeLayer.L3_PRODUCT_LOGIC: "l3-product-logic",
    KnowledgeLayer.L4_USER_KNOWLEDGE: "l4-user-knowledge",
}


@dataclass(frozen=True)
class PublishWrite:
    path: Path
    item: KnowledgeItem


@dataclass(frozen=True)
class PublishPlan:
    writes: tuple[PublishWrite, ...]
    deletes: tuple[Path, ...]
    index_upsert_ids: tuple[str, ...]
    index_delete_ids: tuple[str, ...]


def _statement(item: KnowledgeItem) -> str:
    lines = item.content.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def _frontmatter(item: KnowledgeItem) -> dict[str, object]:
    metadata: dict[str, object] = {
        "id": item.id,
        "layer": item.layer.value,
        "module": item.module,
    }
    if item.feature is not None:
        metadata["feature"] = item.feature
    metadata["status"] = item.status.value
    metadata["version"] = item.version
    if item.derived_from:
        metadata["derived_from"] = list(item.derived_from)
    if item.behavior_rule_id:
        metadata["behavior_rule_id"] = item.behavior_rule_id
    if item.sources:
        metadata["sources"] = [
            {
                key: value
                for key, value in source.model_dump(mode="json").items()
                if value is not None
            }
            for source in item.sources
        ]
    if item.tags:
        metadata["tags"] = list(item.tags)
    if item.visible_roles:
        metadata["visible_roles"] = [role.value for role in item.visible_roles]
    return metadata


def render_knowledge_item(item: KnowledgeItem) -> str:
    frontmatter = yaml.safe_dump(
        _frontmatter(item),
        allow_unicode=True,
        sort_keys=False,
    ).strip()
    body = _statement(item)
    suffix = f"\n\n{body}" if body else ""
    return f"---\n{frontmatter}\n---\n\n# {item.title.strip()}{suffix}\n"


def _knowledge_paths(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in sorted(root.rglob("*.md")):
        if path.name == "README.md":
            continue
        item = load_knowledge_file(path)
        if item.id in paths:
            raise ValueError(f"duplicate knowledge id on disk: {item.id}")
        paths[item.id] = path
    return paths


def _default_path(root: Path, item: KnowledgeItem) -> Path:
    layer_dir = _LAYER_DIRS[item.layer]
    product = item.module.split(".", 1)[0].strip()
    if not product:
        raise ValueError(f"cannot infer knowledge product directory: {item.id}")
    feature = (item.feature or "general").replace("_", "-")
    key = item.id.rsplit(".", 1)[-1].replace("_", "-")
    return root / layer_dir / product / feature / f"{key}.md"


def _change_map(preview: dict[str, object], key: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in preview.get(key, []):
        if not isinstance(raw, dict):
            raise ValueError(f"{key} must contain objects")
        knowledge_id = raw.get("id")
        change = raw.get("change")
        if not isinstance(knowledge_id, str) or not isinstance(change, str):
            raise ValueError(f"invalid {key} entry")
        if knowledge_id in result:
            raise ValueError(f"duplicate {key} id: {knowledge_id}")
        result[knowledge_id] = change
    return result


def _items_map(preview: dict[str, object], key: str) -> dict[str, KnowledgeItem]:
    result: dict[str, KnowledgeItem] = {}
    for raw in preview.get(key, []):
        item = KnowledgeItem.model_validate(raw)
        if item.id in result:
            raise ValueError(f"duplicate {key} id: {item.id}")
        result[item.id] = item
    return result


def plan_regeneration_publish(
    preview: dict[str, object],
    *,
    knowledge_root: str | Path,
) -> PublishPlan:
    root = Path(knowledge_root)
    catalog = KnowledgeCatalog.from_directory(root)
    existing_paths = _knowledge_paths(root)
    l1_changes = _change_map(preview, "l1_changes")
    l2_changes = _change_map(preview, "l2_changes")
    l1_items = _items_map(preview, "l1_items")
    l2_items = _items_map(preview, "l2_items")
    l3_changes = _change_map(preview, "l3_changes")
    l4_changes = _change_map(preview, "l4_changes")
    l3_items = _items_map(preview, "l3_items")
    l4_items = _items_map(preview, "l4_items")

    writes: dict[Path, KnowledgeItem] = {}
    deletes: set[Path] = set()
    upsert_ids: set[str] = set()
    delete_ids: set[str] = set()

    # All surviving L1 items are rewritten because even semantically unchanged
    # facts may have a new SourceBinding commit/file/line.
    for knowledge_id, item in l1_items.items():
        if l1_changes.get(knowledge_id) == "removed":
            raise ValueError(f"removed L1 must not appear in l1_items: {knowledge_id}")
        path = existing_paths.get(knowledge_id) or _default_path(root, item)
        writes[path] = item
        upsert_ids.add(knowledge_id)

    for knowledge_id, change in l1_changes.items():
        if change == "removed":
            path = existing_paths.get(knowledge_id)
            if path is None:
                raise ValueError(f"cannot remove missing L1 knowledge: {knowledge_id}")
            deletes.add(path)
            delete_ids.add(knowledge_id)
        elif knowledge_id not in l1_items:
            raise ValueError(f"surviving L1 missing from l1_items: {knowledge_id}")

    for knowledge_id, change in l2_changes.items():
        if change == "removed":
            path = existing_paths.get(knowledge_id)
            if path is None:
                raise ValueError(f"cannot remove missing L2 knowledge: {knowledge_id}")
            deletes.add(path)
            delete_ids.add(knowledge_id)
            continue
        if change == "unchanged":
            continue
        item = l2_items.get(knowledge_id)
        if item is None:
            raise ValueError(f"changed L2 missing from l2_items: {knowledge_id}")
        path = existing_paths.get(knowledge_id) or _default_path(root, item)
        writes[path] = item
        upsert_ids.add(knowledge_id)

    for layer, changes, items in (
        (KnowledgeLayer.L3_PRODUCT_LOGIC, l3_changes, l3_items),
        (KnowledgeLayer.L4_USER_KNOWLEDGE, l4_changes, l4_items),
    ):
        for knowledge_id, change in changes.items():
            if change == "removed":
                path = existing_paths.get(knowledge_id)
                if path is None:
                    raise ValueError(f"cannot remove missing {layer.value} knowledge: {knowledge_id}")
                deletes.add(path)
                delete_ids.add(knowledge_id)
                continue
            item = items.get(knowledge_id)
            if item is None:
                raise ValueError(f"changed {layer.value} missing from items: {knowledge_id}")
            if item.layer != layer:
                raise ValueError(f"{knowledge_id} is not {layer.value} knowledge")
            path = existing_paths.get(knowledge_id) or _default_path(root, item)
            writes[path] = item
            upsert_ids.add(knowledge_id)

    l3_review = preview.get("l3_review", [])
    if not isinstance(l3_review, list):
        raise ValueError("l3_review must be a list")
    review_roots: list[str] = []
    for knowledge_id in l3_review:
        if not isinstance(knowledge_id, str):
            raise ValueError("l3_review must contain knowledge ids")
        path = existing_paths.get(knowledge_id)
        if path is None:
            raise ValueError(f"cannot route missing L3 to review: {knowledge_id}")
        item = load_knowledge_file(path)
        if item.layer != KnowledgeLayer.L3_PRODUCT_LOGIC:
            raise ValueError(f"l3_review contains non-L3 knowledge: {knowledge_id}")
        if item.status == KnowledgeStatus.DEPRECATED:
            continue
        review_roots.append(knowledge_id)
        if item.status != KnowledgeStatus.REVIEW:
            item = item.model_copy(update={"status": KnowledgeStatus.REVIEW})
            writes[path] = item
            upsert_ids.add(knowledge_id)

    # A product-logic change makes already-published user knowledge derived
    # from it unsafe to serve until L4 is regenerated/reviewed.
    for item in upstream_items(catalog, review_roots):
        if (
            item.layer != KnowledgeLayer.L4_USER_KNOWLEDGE
            or item.status != KnowledgeStatus.PUBLISHED
        ):
            continue
        path = existing_paths.get(item.id)
        if path is None:
            raise ValueError(f"cannot invalidate missing L4 knowledge: {item.id}")
        writes[path] = item.model_copy(update={"status": KnowledgeStatus.OUTDATED})
        upsert_ids.add(item.id)

    overlap = set(writes) & deletes
    if overlap:
        raise ValueError("publish plan writes and deletes the same path")

    return PublishPlan(
        writes=tuple(
            PublishWrite(path=path, item=item)
            for path, item in sorted(writes.items(), key=lambda pair: str(pair[0]))
        ),
        deletes=tuple(sorted(deletes, key=str)),
        index_upsert_ids=tuple(sorted(upsert_ids)),
        index_delete_ids=tuple(sorted(delete_ids)),
    )


def apply_publish_plan(plan: PublishPlan) -> dict[str, list[str]]:
    missing = [path for path in plan.deletes if not path.exists()]
    if missing:
        raise ValueError(f"knowledge file disappeared before publish: {missing[0]}")

    for write in plan.writes:
        write.path.parent.mkdir(parents=True, exist_ok=True)
        write.path.write_text(render_knowledge_item(write.item), encoding="utf-8")
    for path in plan.deletes:
        path.unlink()
    return {
        "written": [str(write.path) for write in plan.writes],
        "deleted": [str(path) for path in plan.deletes],
        "index_upsert_ids": list(plan.index_upsert_ids),
        "index_delete_ids": list(plan.index_delete_ids),
    }
