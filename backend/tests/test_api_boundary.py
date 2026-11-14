"""The backend API no longer serves browser pages or public OIDC configuration."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_backend_does_not_serve_frontend_or_spa_config() -> None:
    with TestClient(app) as client:
        assert client.get("/").status_code == 404
        assert client.get("/config.json").status_code == 404


def test_human_api_rejects_missing_bearer_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
