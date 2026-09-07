from __future__ import annotations

import time
from pathlib import Path

import yaml

from app.knowledge.models import KnowledgeItem, SourceBinding


_catalog_cache: dict[str, tuple[tuple[tuple[str, int, int], ...], "KnowledgeCatalog", float]] = {}
_CATALOG_TTL_SECONDS = 2.0


def _directory_fingerprint(root: Path) -> tuple[tuple[str, int, int], ...]:
    files = sorted(
        path for path in root.rglob("*.md") if path.name != "README.md"
    )
    return tuple(
        (str(path.relative_to(root)), path.stat().st_mtime_ns, path.stat().st_size)
        for path in files
    )


class KnowledgeCatalog:
    def __init__(self, items: list[KnowledgeItem]) -> None:
        self._items = {item.id: item for item in items}
        if len(self._items) != len(items):
            raise ValueError("duplicate knowledge id")

    @classmethod
    def from_directory(cls, root: str | Path) -> "KnowledgeCatalog":
        """Load with a process-level cache invalidated by file mtime/size.

        The knowledge directory is the source of truth; this cache only avoids
        re-parsing every Markdown file on every request when nothing changed."""
        root_path = Path(root)
        key = str(root_path)
        cached = _catalog_cache.get(key)
        now = time.monotonic()
        if cached is not None and now - cached[2] < _CATALOG_TTL_SECONDS:
            return cached[1]
        fingerprint = _directory_fingerprint(root_path)
        if cached is not None and cached[0] == fingerprint:
            _catalog_cache[key] = (fingerprint, cached[1], now)
            return cached[1]
        items = [
            load_knowledge_file(path)
            for path in sorted(root_path.rglob("*.md"))
            if path.name != "README.md"
        ]
        catalog = cls(items)
        _catalog_cache[key] = (fingerprint, catalog, now)
        return catalog

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


def _markdown_title(body: str, file_path: Path) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    raise ValueError(f"knowledge file has no title field or Markdown H1: {file_path}")


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

    body = body.strip()
    title = metadata.get("title") or _markdown_title(body, file_path)
    return KnowledgeItem.model_validate({**metadata, "title": title, "content": body})
