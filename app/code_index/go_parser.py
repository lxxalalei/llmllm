from __future__ import annotations

import tree_sitter_go
from tree_sitter import Language, Parser

from app.code_index.models import Symbol


class GoCodeParser:
    """Tree-sitter adapter for top-level Go functions and methods."""

    def __init__(self) -> None:
        language = Language(tree_sitter_go.language())
        try:
            self._parser = Parser(language)
        except TypeError:
            self._parser = Parser()
            self._parser.set_language(language)

    def extract_symbols(self, source: str) -> list[Symbol]:
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        symbols: list[Symbol] = []

        for node in tree.root_node.children:
            if node.type not in {"function_declaration", "method_declaration"}:
                continue
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            symbols.append(
                Symbol(
                    kind=node.type,
                    name=source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8"),
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    source=source_bytes[node.start_byte:node.end_byte].decode("utf-8"),
                )
            )

        return symbols
