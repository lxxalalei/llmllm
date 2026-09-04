from __future__ import annotations

from dataclasses import asdict
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.code_index import GoCodeParser, PythonCodeParser


class CompilerState(TypedDict):
    source: str
    events: list[str]
    artifacts: list[str]
    language: NotRequired[str]
    content: NotRequired[str]
    symbols: NotRequired[list[dict[str, object]]]


def _event(state: CompilerState, event: str, artifact: str | None = None) -> CompilerState:
    artifacts = list(state["artifacts"])
    if artifact:
        artifacts.append(artifact)
    return {
        **state,
        "events": [*state["events"], event],
        "artifacts": artifacts,
    }


def _resolve_language(source: str, language: str | None) -> str | None:
    if language:
        return language.lower()
    if source.endswith(".go"):
        return "go"
    if source.endswith(".py"):
        return "python"
    return None


async def analyze_source(state: CompilerState) -> CompilerState:
    content = state.get("content")
    language = _resolve_language(state["source"], state.get("language"))

    if not content:
        return _event(state, "source_analyzed")

    if language == "go":
        parser = GoCodeParser()
    elif language == "python":
        parser = PythonCodeParser()
    else:
        raise ValueError("language is required for source content unless the file extension is .go or .py")

    symbols = [asdict(symbol) for symbol in parser.extract_symbols(content)]
    return _event({**state, "language": language, "symbols": symbols}, "source_analyzed")


async def build_l1(state: CompilerState) -> CompilerState:
    return _event(state, "l1_generated", "L1")


async def build_l2(state: CompilerState) -> CompilerState:
    return _event(state, "l2_generated", "L2")


async def build_l3(state: CompilerState) -> CompilerState:
    return _event(state, "l3_generated_requires_review", "L3")


async def build_l4(state: CompilerState) -> CompilerState:
    return _event(state, "l4_generated", "L4")


def build_compiler_graph():
    """Build the V1 compiler workflow.

    Source analysis is real: supplied Python/Go content is parsed into symbols.
    L1-L4 generation remains an explicit orchestration boundary until a real
    generator is connected; long-term knowledge assets live outside graph state.
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
