from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.knowledge import KnowledgeCatalog
from app.knowledge.impact import analyze_impact, apply_transitions

KNOWLEDGE_ROOT = Path("knowledge")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze code-change impact on knowledge assets (M4)")
    parser.add_argument("--old", type=Path, required=True, help="old source file (pinned commit)")
    parser.add_argument("--new", type=Path, required=True, help="new source file (changed sample)")
    parser.add_argument("--commit", default=None, help="restrict L1 binding to this commit")
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_ROOT)
    parser.add_argument("--apply", action="store_true", help="apply proposed status transitions to assets")
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args()

    catalog = KnowledgeCatalog.from_directory(args.knowledge_root)
    old_source = args.old.read_text(encoding="utf-8")
    new_source = args.new.read_text(encoding="utf-8")
    report = analyze_impact(catalog, old_source, new_source, commit=args.commit)

    if args.apply:
        report["applied_files"] = apply_transitions(args.knowledge_root, report["transitions"])

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
