import asyncio

from app.workflows.compiler import build_compiler_graph


def test_compiler_does_not_claim_placeholder_generation() -> None:
    result = asyncio.run(
        build_compiler_graph().ainvoke(
            {"source": "conversation/archive_service.py", "events": [], "artifacts": []}
        )
    )

    assert result["events"] == [
        "source_skipped_no_content",
        "l1_skipped_no_symbols",
        "l2_not_implemented",
        "l3_not_implemented",
        "l4_not_implemented",
    ]
    assert result["artifacts"] == []


def test_compiler_analyzes_go_source_without_claiming_l1() -> None:
    result = asyncio.run(
        build_compiler_graph().ainvoke(
            {
                "source": "server/channels/app/channel.go",
                "content": """
package app

func (a *App) CreateChannelWithUser() {}
func (a *App) CreateChannel() {}
""".strip(),
                "events": [],
                "artifacts": [],
            }
        )
    )

    assert result["language"] == "go"
    assert [symbol["name"] for symbol in result["symbols"]] == ["CreateChannelWithUser", "CreateChannel"]
    assert result["events"] == [
        "source_analyzed",
        "l1_skipped_no_provider",
        "l2_not_implemented",
        "l3_not_implemented",
        "l4_not_implemented",
    ]
    assert result["artifacts"] == []
