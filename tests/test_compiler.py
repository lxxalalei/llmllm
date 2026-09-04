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
