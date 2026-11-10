"""Security-focused tests for the internal BFF session store."""
from __future__ import annotations

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.core.config import get_settings
from app.core.database import get_session
from app.identity.bff_sessions import _decrypt, _encrypt, router


@pytest.fixture(autouse=True)
def _bff_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BFF_INTERNAL_SECRET", "test-internal-secret-value")
    monkeypatch.setenv("BFF_SESSION_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_session_tokens_are_encrypted_at_rest() -> None:
    token = "sensitive-access-token"
    ciphertext = _encrypt(token)
    assert ciphertext != token
    assert token not in ciphertext
    assert _decrypt(ciphertext) == token


def test_internal_session_routes_reject_missing_secret() -> None:
    async def fake_session():
        yield object()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = fake_session

    response = TestClient(app).get("/internal/v1/bff/sessions/" + ("a" * 64))
    assert response.status_code == 401
    assert response.json()["detail"] == "bff_internal_auth_required"


def test_internal_session_routes_reject_wrong_secret() -> None:
    async def fake_session():
        yield object()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = fake_session

    response = TestClient(app).get(
        "/internal/v1/bff/sessions/" + ("a" * 64),
        headers={"X-NetPay-BFF-Secret": "wrong-secret"},
    )
    assert response.status_code == 401
