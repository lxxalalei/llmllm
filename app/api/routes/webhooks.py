from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.integrations.github import GitHubSourceClient, analyze_repository_change
from app.knowledge import KnowledgeCatalog

router = APIRouter()
KNOWLEDGE_ROOT = Path("knowledge")


class GitHubRepository(BaseModel):
    full_name: str


class GitHubPushPayload(BaseModel):
    before: str
    after: str
    repository: GitHubRepository
    ref: str | None = None


@router.post("/github")
async def github_push(
    payload: GitHubPushPayload,
    event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
) -> dict[str, object]:
    if event is not None and event != "push":
        raise HTTPException(status_code=400, detail="only GitHub push events are supported")
    if payload.before == "0" * 40:
        raise HTTPException(
            status_code=422,
            detail="initial branch push has no before commit to compare",
        )

    catalog = KnowledgeCatalog.from_directory(KNOWLEDGE_ROOT)
    client = GitHubSourceClient(token=settings.github_token)
    try:
        return await analyze_repository_change(
            catalog,
            repository=payload.repository.full_name,
            before=payload.before,
            after=payload.after,
            client=client,
        )
    finally:
        await client.close()
