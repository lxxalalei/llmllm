from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.code_index.inventory import inventory_repository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory supported source files and top-level symbols in a repository scope"
    )
    parser.add_argument("repository_root", type=Path)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional repository-relative files/directories; defaults to the whole repository",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = inventory_repository(
        args.repository_root,
        paths=args.paths or None,
    ).to_dict()
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
