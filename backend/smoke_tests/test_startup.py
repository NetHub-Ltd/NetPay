"""Focused tests for runtime dependency checks and FastAPI lifespan behavior.

These tests deliberately live outside backend/tests to avoid loading the legacy
integration-test conftest. No migrations or schema creation are performed here.
"""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import check_database, dispose_engine


def test_lifespan_checks_database_and_redis_then_closes_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    real_check_database = main.check_database
    real_dispose_engine = main.dispose_engine

    async def database_check() -> None:
        calls.append("database")
        await real_check_database()

    async def redis_check() -> None:
        calls.append("redis")

    async def redis_dispose() -> None:
        calls.append("close_redis")

    async def database_dispose() -> None:
        calls.append("close_database")
        await real_dispose_engine()

    monkeypatch.setattr(main, "check_database", database_check)
    monkeypatch.setattr(main, "check_redis", redis_check)
    monkeypatch.setattr(main, "dispose_redis", redis_dispose)
    monkeypatch.setattr(main, "dispose_engine", database_dispose)

    with TestClient(main.app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    assert calls == ["database", "redis", "close_redis", "close_database"]


def test_redis_failure_is_non_fatal_but_database_is_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def database_check() -> None:
        calls.append("database")

    async def redis_check() -> None:
        calls.append("redis")
        raise ConnectionError("private redis endpoint detail")

    async def no_op() -> None:
        return None

    monkeypatch.setattr(main, "check_database", database_check)
    monkeypatch.setattr(main, "check_redis", redis_check)
    monkeypatch.setattr(main, "dispose_redis", no_op)
    monkeypatch.setattr(main, "dispose_engine", no_op)

    with TestClient(main.app) as client:
        assert client.get("/health/live").status_code == 200

    assert calls == ["database", "redis"]


def test_database_failure_aborts_startup_and_still_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def database_check() -> None:
        calls.append("database")
        raise ConnectionError("private database endpoint detail")

    async def redis_check() -> None:
        calls.append("redis")

    async def redis_dispose() -> None:
        calls.append("close_redis")

    async def database_dispose() -> None:
        calls.append("close_database")

    monkeypatch.setattr(main, "check_database", database_check)
    monkeypatch.setattr(main, "check_redis", redis_check)
    monkeypatch.setattr(main, "dispose_redis", redis_dispose)
    monkeypatch.setattr(main, "dispose_engine", database_dispose)

    with pytest.raises(ConnectionError):
        with TestClient(main.app):
            pass

    assert calls == ["database", "close_redis", "close_database"]


@pytest.mark.asyncio
async def test_database_connectivity_check_executes_query() -> None:
    # The CI database URL is an isolated in-memory SQLite database; this tests
    # the actual SQLAlchemy connection path without migrations or external state.
    try:
        await check_database()
    finally:
        await dispose_engine()


@pytest.mark.asyncio
async def test_redis_connectivity_check_pings_configured_service() -> None:
    from app.redis_client import check_redis, dispose_redis

    try:
        await check_redis()
    finally:
        await dispose_redis()
