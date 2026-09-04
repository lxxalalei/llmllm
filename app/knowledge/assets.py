from __future__ import annotations

from pathlib import Path

import yaml

from app.knowledge.models import KnowledgeItem, SourceBinding


class KnowledgeCatalog:
    def __init__(self, items: list[KnowledgeItem]) -> None:
        self._items = {item.id: item for item in items}
        if len(self._items) != len(items):
            raise ValueError("duplicate knowledge id")

    @classmethod
    def from_directory(cls, root: str | Path) -> "KnowledgeCatalog":
        root_path = Path(root)
        items = [load_knowledge_file(path) for path in sorted(root_path.rglob("*.md")) if path.name != "README.md"]
        return cls(items)

    def get(self, knowledge_id: str) -> KnowledgeItem:
        try:
            return self._items[knowledge_id]
        except KeyError as exc:
            raise KeyError(f"unknown knowledge id: {knowledge_id}") from exc

    def trace_lineage(self, knowledge_id: str) -> list[KnowledgeItem]:
        lineage: list[KnowledgeItem] = []
        visited: set[str] = set()

        def visit(current_id: str) -> None:
            if current_id in visited:
                return
            visited.add(current_id)
            item = self.get(current_id)
            lineage.append(item)
            for parent_id in item.derived_from:
                visit(parent_id)

        visit(knowledge_id)
        return lineage

    def trace_sources(self, knowledge_id: str) -> list[SourceBinding]:
        sources: list[SourceBinding] = []
        seen: set[tuple[str, str | None, str | None, str, str | None]] = set()
        for item in self.trace_lineage(knowledge_id):
            for source in item.sources:
                key = (source.repo, source.ref, source.commit, source.file, source.symbol)
                if key in seen:
                    continue
                seen.add(key)
                sources.append(source)
        return sources


def load_knowledge_file(path: str | Path) -> KnowledgeItem:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"knowledge file has no YAML frontmatter: {file_path}")

    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"invalid YAML frontmatter boundary: {file_path}") from exc

    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise ValueError(f"knowledge frontmatter must be a mapping: {file_path}")

    return KnowledgeItem.model_validate({**metadata, "content": body.strip()})
