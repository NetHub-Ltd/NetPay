"""Fresh startup smoke tests for the rebuilt NetPay API."""

from fastapi.testclient import TestClient

from app.main import app


def test_application_starts_and_exposes_openapi() -> None:
    """The ASGI app initializes and its OpenAPI document is available."""
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "NetPay API"


def test_liveness_endpoint() -> None:
    """The liveness probe responds successfully without external services."""
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_is_dependency_free_for_bootstrap() -> None:
    """Initial readiness stays independent of the database stage."""
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
