import asyncio

from app.workflows.compiler import build_compiler_graph


def test_compiler_pipeline_order() -> None:
    graph = build_compiler_graph()
    result = asyncio.run(
        graph.ainvoke(
            {
                "source": "conversation/archive_service.py",
                "events": [],
                "artifacts": [],
            }
        )
    )

    assert result["events"] == [
        "source_analyzed",
        "l1_generated",
        "l2_generated",
        "l3_generated_requires_review",
        "l4_generated",
    ]
    assert result["artifacts"] == ["L1", "L2", "L3", "L4"]


def test_compiler_analyzes_go_source_content() -> None:
    graph = build_compiler_graph()
    result = asyncio.run(
        graph.ainvoke(
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
    assert [symbol["name"] for symbol in result["symbols"]] == [
        "CreateChannelWithUser",
        "CreateChannel",
    ]
