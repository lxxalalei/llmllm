from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.integrations.github import GitHubSourceClient, analyze_repository_change
from app.knowledge import KnowledgeCatalog

router = APIRouter()
KNOWLEDGE_ROOT = Path("knowledge")
CommitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class GitHubRepository(BaseModel):
    full_name: str


class GitHubPushPayload(BaseModel):
    before: CommitSha
    after: CommitSha
    repository: GitHubRepository
    ref: str | None = None


@router.post("/github")
async def github_push(
    payload: GitHubPushPayload,
    event: Annotated[str, Header(alias="X-GitHub-Event")],
) -> dict[str, object]:
    if event != "push":
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
