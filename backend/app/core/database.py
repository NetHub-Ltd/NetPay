"""Async PostgreSQL engine and request-scoped SQLModel sessions."""
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    """Create a small configurable pool with stale-connection detection.

    Pool limits apply per engine/process. For example, two workers with a pool
    size of one can retain two idle PostgreSQL connections in total.
    """
    return create_async_engine(
        settings.async_database_url(),
        pool_pre_ping=True,
        pool_use_lifo=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
    )


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
