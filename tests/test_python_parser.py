from app.code_index import PythonCodeParser


def test_extract_top_level_symbols() -> None:
    parser = PythonCodeParser()
    symbols = parser.extract_symbols(
        """
class ConversationService:
    pass

def archive_if_inactive():
    pass
""".strip()
    )

    assert [(s.kind, s.name) for s in symbols] == [
        ("class_definition", "ConversationService"),
        ("function_definition", "archive_if_inactive"),
    ]
