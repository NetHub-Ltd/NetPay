"""Startup smoke tests for the rebuilt NetPay API with real CI services."""
from fastapi.testclient import TestClient
from app.main import app

def test_application_starts_and_exposes_openapi() -> None:
    """The ASGI app starts and serves its OpenAPI document."""
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "NetPay API"

def test_liveness_endpoint() -> None:
    """Liveness reports process health independently of dependency checks."""
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_readiness_requires_database_and_reports_redis() -> None:
    """Readiness confirms PostgreSQL and reports Redis as auxiliary infrastructure."""
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}
