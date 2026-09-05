from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Enterprise product knowledge compiler and role-aware QA service.",
)

app.include_router(api_router)


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def chat_index() -> str:
    html_path = Path(__file__).parent / "web" / "chat.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}
