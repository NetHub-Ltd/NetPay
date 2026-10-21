"""Async PostgreSQL engine and request-scoped SQLModel sessions."""
from collections.abc import AsyncIterator
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import Settings

def create_database_engine(settings: Settings) -> AsyncEngine:
    """Create a bounded async engine with stale-connection detection."""
    return create_async_engine(settings.database_url.get_secret_value(), pool_pre_ping=True, pool_size=5, max_overflow=5, pool_timeout=10, pool_recycle=1800)

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build a factory for request-scoped sessions."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_database(engine: AsyncEngine) -> None:
    """Raise if PostgreSQL cannot answer a simple health query."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one session per request and always close it afterward."""
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise RuntimeError("Database session factory is not initialized")
    async with factory() as session:
        yield session
