"""Async database engine and readiness check.

PostgreSQL is the production source of truth. SQLite remains useful for fast
unit tests; migrations and production deployment will use PostgreSQL.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=False,
        )
    return _engine


async def check_database() -> None:
    """Raise if the configured database cannot answer a trivial query."""
    async with get_engine().connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
