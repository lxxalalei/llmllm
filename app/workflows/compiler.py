from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CompilerState(TypedDict):
    source: str
    events: list[str]
    artifacts: list[str]


def _event(state: CompilerState, event: str, artifact: str | None = None) -> CompilerState:
    artifacts = list(state["artifacts"])
    if artifact:
        artifacts.append(artifact)
    return {
        "source": state["source"],
        "events": [*state["events"], event],
        "artifacts": artifacts,
    }


async def analyze_source(state: CompilerState) -> CompilerState:
    return _event(state, "source_analyzed")


async def build_l1(state: CompilerState) -> CompilerState:
    return _event(state, "l1_generated", "L1")


async def build_l2(state: CompilerState) -> CompilerState:
    return _event(state, "l2_generated", "L2")


async def build_l3(state: CompilerState) -> CompilerState:
    return _event(state, "l3_generated_requires_review", "L3")


async def build_l4(state: CompilerState) -> CompilerState:
    return _event(state, "l4_generated", "L4")


def build_compiler_graph():
    """Build the deterministic V1 compiler skeleton.

    The bootstrap intentionally does not call an LLM. Each node is a stable
    orchestration boundary where a real analyzer/generator will be injected.
    """
    graph = StateGraph(CompilerState)
    graph.add_node("analyze_source", analyze_source)
    graph.add_node("build_l1", build_l1)
    graph.add_node("build_l2", build_l2)
    graph.add_node("build_l3", build_l3)
    graph.add_node("build_l4", build_l4)
    graph.add_edge(START, "analyze_source")
    graph.add_edge("analyze_source", "build_l1")
    graph.add_edge("build_l1", "build_l2")
    graph.add_edge("build_l2", "build_l3")
    graph.add_edge("build_l3", "build_l4")
    graph.add_edge("build_l4", END)
    return graph.compile()
