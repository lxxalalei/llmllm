from fastapi import APIRouter
from pydantic import BaseModel

from app.workflows.compiler import build_compiler_graph

router = APIRouter()


class CompilerPreviewRequest(BaseModel):
    source: str
    language: str | None = None
    content: str | None = None
    repo: str | None = None
    ref: str | None = None
    commit: str | None = None
    module: str | None = None
    feature: str | None = None
    namespace: str | None = None
    target_symbols: list[str] = []


class CompilerPreviewResponse(BaseModel):
    source: str
    language: str | None = None
    symbols: list[dict[str, object]]
    l1_items: list[dict[str, object]]
    events: list[str]
    artifacts: list[str]


@router.post("/preview", response_model=CompilerPreviewResponse)
async def compiler_preview(payload: CompilerPreviewRequest) -> CompilerPreviewResponse:
    state = {
        "source": payload.source,
        "events": [],
        "artifacts": [],
    }
    for field in ("language", "content", "repo", "ref", "commit", "module", "feature", "namespace"):
        value = getattr(payload, field)
        if value is not None:
            state[field] = value
    if payload.target_symbols:
        state["target_symbols"] = payload.target_symbols

    result = await build_compiler_graph().ainvoke(state)
    return CompilerPreviewResponse(
        source=result["source"],
        language=result.get("language"),
        symbols=result.get("symbols", []),
        l1_items=result.get("l1_items", []),
        events=result["events"],
        artifacts=result["artifacts"],
    )
