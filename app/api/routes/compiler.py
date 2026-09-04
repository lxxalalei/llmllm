from fastapi import APIRouter
from pydantic import BaseModel

from app.workflows.compiler import build_compiler_graph

router = APIRouter()


class CompilerPreviewRequest(BaseModel):
    source: str


class CompilerPreviewResponse(BaseModel):
    source: str
    events: list[str]
    artifacts: list[str]


@router.post("/preview", response_model=CompilerPreviewResponse)
async def compiler_preview(payload: CompilerPreviewRequest) -> CompilerPreviewResponse:
    graph = build_compiler_graph()
    result = await graph.ainvoke(
        {
            "source": payload.source,
            "events": [],
            "artifacts": [],
        }
    )
    return CompilerPreviewResponse(
        source=result["source"],
        events=result["events"],
        artifacts=result["artifacts"],
    )
