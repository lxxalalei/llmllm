from __future__ import annotations

from dataclasses import asdict
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.code_index import GoCodeParser, PythonCodeParser, Symbol
from app.core.config import settings
from app.knowledge.l1_generator import L1Generator
from app.llm import OpenAIEngineeringFactExtractor


class CompilerState(TypedDict):
    source: str
    events: list[str]
    artifacts: list[str]
    language: NotRequired[str]
    content: NotRequired[str]
    symbols: NotRequired[list[dict[str, object]]]
    repo: NotRequired[str]
    ref: NotRequired[str]
    commit: NotRequired[str]
    module: NotRequired[str]
    feature: NotRequired[str]
    namespace: NotRequired[str]
    target_symbols: NotRequired[list[str]]
    l1_items: NotRequired[list[dict[str, object]]]


def _event(state: CompilerState, event: str, artifact: str | None = None) -> CompilerState:
    artifacts = list(state["artifacts"])
    if artifact:
        artifacts.append(artifact)
    return {**state, "events": [*state["events"], event], "artifacts": artifacts}


def _resolve_language(source: str, language: str | None) -> str | None:
    if language:
        return language.lower()
    if source.endswith(".go"):
        return "go"
    if source.endswith(".py"):
        return "python"
    return None


def _configured_l1_generator() -> L1Generator | None:
    if settings.llm_provider is None:
        return None
    if settings.llm_provider.lower() != "openai":
        raise ValueError(f"unsupported LLM provider: {settings.llm_provider}")
    if not settings.llm_api_key or not settings.llm_model:
        raise ValueError("LLM_API_KEY and LLM_MODEL are required when LLM_PROVIDER=openai")
    return L1Generator(
        OpenAIEngineeringFactExtractor(
            api_key=settings.llm_api_key, model=settings.llm_model, base_url=settings.llm_base_url
        )
    )


async def analyze_source(state: CompilerState) -> CompilerState:
    content = state.get("content")
    language = _resolve_language(state["source"], state.get("language"))
    if not content:
        return _event(state, "source_skipped_no_content")

    if language == "go":
        parser = GoCodeParser()
    elif language == "python":
        parser = PythonCodeParser()
    else:
        raise ValueError("language is required for source content unless the file extension is .go or .py")

    symbols = [asdict(symbol) for symbol in parser.extract_symbols(content)]
    return _event({**state, "language": language, "symbols": symbols}, "source_analyzed")


async def build_l1(state: CompilerState) -> CompilerState:
    if not state.get("symbols"):
        return _event(state, "l1_skipped_no_symbols")

    generator = _configured_l1_generator()
    if generator is None:
        return _event(state, "l1_skipped_no_provider")

    required_metadata = ("repo", "module", "feature", "namespace")
    missing = [field for field in required_metadata if not state.get(field)]
    if missing:
        raise ValueError(f"missing L1 source metadata: {', '.join(missing)}")

    parsed_symbols = [Symbol(**symbol) for symbol in state["symbols"]]
    targets = set(state.get("target_symbols", []))
    if targets:
        parsed_symbols = [symbol for symbol in parsed_symbols if symbol.name in targets]
        missing_targets = targets - {symbol.name for symbol in parsed_symbols}
        if missing_targets:
            raise ValueError(f"target symbols not found: {', '.join(sorted(missing_targets))}")

    items = await generator.generate(
        namespace=state["namespace"],
        module=state["module"],
        feature=state["feature"],
        repo=state["repo"],
        ref=state.get("ref"),
        commit=state.get("commit"),
        file=state["source"],
        symbols=parsed_symbols,
    )
    return _event({**state, "l1_items": [item.model_dump(mode="json") for item in items]}, "l1_generated", "L1")


async def build_l2(state: CompilerState) -> CompilerState:
    return _event(state, "l2_not_implemented")


async def build_l3(state: CompilerState) -> CompilerState:
    return _event(state, "l3_not_implemented")


async def build_l4(state: CompilerState) -> CompilerState:
    return _event(state, "l4_not_implemented")


def build_compiler_graph():
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
