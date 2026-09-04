from fastapi import APIRouter
from pydantic import BaseModel

from app.workflows.compiler import build_compiler_graph

router = APIRouter()


class CompilerPreviewRequest(BaseModel):
    source: str
    language: str | None = None
    content: str | None = None


class CompilerPreviewResponse(BaseModel):
    source: str
    language: str | None = None
    symbols: list[dict[str, object]]
    events: list[str]
    artifacts: list[str]


@router.post("/preview", response_model=CompilerPreviewResponse)
async def compiler_preview(payload: CompilerPreviewRequest) -> CompilerPreviewResponse:
    graph = build_compiler_graph()
    state: dict[str, object] = {
        "source": payload.source,
        "events": [],
        "artifacts": [],
    }
    if payload.language is not None:
        state["language"] = payload.language
    if payload.content is not None:
        state["content"] = payload.content

    result = await graph.ainvoke(state)
    return CompilerPreviewResponse(
        source=result["source"],
        language=result.get("language"),
        symbols=result.get("symbols", []),
        events=result["events"],
        artifacts=result["artifacts"],
    )
