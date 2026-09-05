from app.code_index import GoCodeParser


def test_extract_top_level_go_functions_and_methods() -> None:
    parser = GoCodeParser()
    symbols = parser.extract_symbols(
        """
package app

func helper() {}

func (a *App) CreateChannel(addMember bool) error {
    return nil
}
""".strip()
    )

    assert [(s.kind, s.name) for s in symbols] == [
        ("function_declaration", "helper"),
        ("method_declaration", "CreateChannel"),
    ]
    assert "func (a *App) CreateChannel" in symbols[1].source
