from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from app.knowledge.batch_compiler import BatchKnowledgeScope
from app.knowledge.domain import KnowledgeDomainManifest, summarize_domain_previews


def _resolve_scope(project_root: Path, scope_path: str) -> Path:
    path = (project_root / scope_path).resolve()
    if not path.is_file():
        raise SystemExit(f"domain scope file not found: {scope_path}")
    return path


def _compile_scope(
    *,
    project_root: Path,
    repository_root: Path,
    scope_path: Path,
    output_path: Path,
) -> dict[str, object]:
    subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "compile_scope.py"),
            str(repository_root),
            str(scope_path),
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        check=True,
    )
    return json.loads(output_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile every feature scope in one mature-product knowledge domain"
    )
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    repository_root = args.repository_root.resolve()
    manifest_path = args.manifest.resolve()
    manifest = KnowledgeDomainManifest.from_file(manifest_path)

    scopes: list[tuple[Path, BatchKnowledgeScope]] = []
    for raw_path in manifest.scopes:
        path = _resolve_scope(project_root, raw_path)
        scope = BatchKnowledgeScope.model_validate_json(path.read_text(encoding="utf-8"))
        if scope.module != manifest.module:
            raise SystemExit(
                f"scope {raw_path} belongs to {scope.module}, expected {manifest.module}"
            )
        scopes.append((path, scope))

    if args.output_dir:
        output_root = args.output_dir.resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix="llmllm-domain-")
        output_root = Path(temp_context.name)

    previews: list[dict[str, object]] = []
    try:
        for scope_path, scope in scopes:
            output_path = output_root / f"{scope.feature}.json"
            previews.append(
                _compile_scope(
                    project_root=project_root,
                    repository_root=repository_root,
                    scope_path=scope_path,
                    output_path=output_path,
                )
            )

        summary = summarize_domain_previews(manifest, previews)
        rendered = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
        if args.summary:
            args.summary.resolve().write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    finally:
        if temp_context is not None:
            temp_context.cleanup()


if __name__ == "__main__":
    main()
