from __future__ import annotations

from dataclasses import dataclass

import tree_sitter_python
from tree_sitter import Language, Parser


@dataclass(slots=True)
class Symbol:
    kind: str
    name: str
    start_line: int
    end_line: int


class PythonCodeParser:
    """Small Tree-sitter adapter used by the bootstrap.

    V1 only extracts top-level class/function names. Cross-file semantic
    analysis is deliberately out of scope for this first scaffold.
    """

    def __init__(self) -> None:
        language = Language(tree_sitter_python.language())
        try:
            self._parser = Parser(language)
        except TypeError:
            self._parser = Parser()
            self._parser.set_language(language)

    def extract_symbols(self, source: str) -> list[Symbol]:
        tree = self._parser.parse(source.encode("utf-8"))
        symbols: list[Symbol] = []
        source_bytes = source.encode("utf-8")

        for node in tree.root_node.children:
            if node.type not in {"class_definition", "function_definition"}:
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
                )
            )

        return symbols
