"""Startup smoke and failure-path tests for the NetPay API."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings
from app.main import app


def test_application_starts_and_exposes_openapi() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "NetPay API"


def test_liveness_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_requires_database_and_reports_redis() -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_database_unavailable_prevents_lifespan_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEngine:
        disposed = False
        async def dispose(self) -> None:
            self.disposed = True

    engine = FakeEngine()
    monkeypatch.setattr(main_module, "get_settings", lambda: Settings(redis_enabled=False))
    monkeypatch.setattr(main_module, "create_database_engine", lambda _settings: engine)
    monkeypatch.setattr(main_module, "create_session_factory", lambda _engine: object())

    async def fail_database_check(_engine: object) -> None:
        raise ConnectionError("database unavailable")

    monkeypatch.setattr(main_module, "check_database", fail_database_check)
    startup_entered = False
    with pytest.raises(ConnectionError, match="database unavailable"):
        async with main_module.lifespan(FastAPI()):
            startup_entered = True
    assert startup_entered is False
    assert engine.disposed is True


def test_readiness_independent_of_nethub_identity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NETHUB_API_BASE_URL", raising=False)
    from app.core.config import get_settings
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"
        assert "nethub" not in body
        assert "oidc" not in body
    finally:
        get_settings.cache_clear()
