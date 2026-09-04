from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Symbol:
    kind: str
    name: str
    start_line: int
    end_line: int
    source: str
