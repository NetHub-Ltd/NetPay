"""Fresh tests for the current FastAPI startup contract.

Kept outside backend/tests so the legacy conftest and its database setup are not
loaded. These tests do not run migrations or connect to a database.
"""
from fastapi.testclient import TestClient

from app.main import app


def test_application_lifespan_starts_and_stops() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_api_root_is_reachable_after_startup() -> None:
    with TestClient(app) as client:
        response = client.get("/api")
        assert response.status_code == 200
        body = response.json()
        assert body["name"]
        assert body["status"] == "running"
        assert body["docs"] == "/docs"
