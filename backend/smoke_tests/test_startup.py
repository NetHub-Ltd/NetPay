"""Backend container startup smoke tests validate API-only runtime."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_backend_does_not_serve_frontend_or_public_oidc_config() -> None:
    client = TestClient(app)
    assert client.get("/").status_code == 404
    assert client.get("/config.json").status_code == 404


def test_human_api_rejects_requests_without_bearer_token() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
