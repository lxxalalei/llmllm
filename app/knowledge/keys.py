from __future__ import annotations

import re


def normalize_knowledge_key(value: object) -> object:
    """Normalize model-proposed CamelCase segments before regex validation.

    Other invalid characters are deliberately preserved so the Pydantic field
    pattern still rejects them. Duplicate canonical IDs remain an explicit
    generator error.
    """
    if not isinstance(value, str):
        return value
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()
