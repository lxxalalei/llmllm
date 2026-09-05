from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool: connections are short-lived and never cross asyncio event loops
# (TestClient portals, reloads). Revisit with a QueuePool once hot paths exist.
engine = create_async_engine(settings.postgres_dsn, poolclass=NullPool, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
