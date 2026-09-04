from fastapi import APIRouter

from app.api.routes.compiler import router as compiler_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
api_router.include_router(compiler_router, prefix="/api/v1/compiler", tags=["compiler"])
