from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from app.code_index.go_parser import GoCodeParser
from app.code_index.python_parser import PythonCodeParser


_EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "vendor", "dist", "build"}


@dataclass(frozen=True)
class InventoryFile:
    path: str
    language: str
    symbols: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class RepositoryInventory:
    root: str
    files: tuple[InventoryFile, ...]

    def to_dict(self) -> dict[str, object]:
        languages = Counter(item.language for item in self.files)
        symbol_count = sum(len(item.symbols) for item in self.files)
        return {
            "root": self.root,
            "summary": {
                "files": len(self.files),
                "symbols": symbol_count,
                "languages": dict(sorted(languages.items())),
            },
            "files": [
                {
                    "path": item.path,
                    "language": item.language,
                    "symbols": list(item.symbols),
                }
                for item in self.files
            ],
        }


def _parser_for(path: Path):
    if path.suffix == ".go":
        return "go", GoCodeParser()
    if path.suffix == ".py":
        return "python", PythonCodeParser()
    return None


def _excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in _EXCLUDED_DIRS for part in relative.parts[:-1])


def _candidate_files(root: Path, paths: list[str] | None) -> list[Path]:
    targets = [root / value for value in paths] if paths else [root]
    candidates: set[Path] = set()
    for target in targets:
        if not target.exists():
            raise ValueError(f"inventory path does not exist: {target}")
        if target.is_file():
            candidates.add(target)
            continue
        for path in target.rglob("*"):
            if path.is_file() and not _excluded(path, root):
                candidates.add(path)
    return sorted(candidates)


def inventory_repository(
    root: str | Path,
    *,
    paths: list[str] | None = None,
) -> RepositoryInventory:
    repository_root = Path(root).resolve()
    if not repository_root.is_dir():
        raise ValueError(f"repository root is not a directory: {repository_root}")

    files: list[InventoryFile] = []
    for path in _candidate_files(repository_root, paths):
        parser_info = _parser_for(path)
        if parser_info is None:
            continue
        language, parser = parser_info
        source = path.read_text(encoding="utf-8")
        symbols = tuple(
            {
                "kind": symbol.kind,
                "name": symbol.name,
                "start_line": symbol.start_line,
                "end_line": symbol.end_line,
            }
            for symbol in parser.extract_symbols(source)
        )
        files.append(
            InventoryFile(
                path=path.relative_to(repository_root).as_posix(),
                language=language,
                symbols=symbols,
            )
        )

    return RepositoryInventory(root=str(repository_root), files=tuple(files))
