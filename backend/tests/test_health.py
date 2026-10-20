from fastapi.testclient import TestClient

from app.main import app


def test_liveness_does_not_require_database() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_root_exposes_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/api")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
