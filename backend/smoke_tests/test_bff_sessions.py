"""Security-focused tests for the internal BFF session store."""
from __future__ import annotations

from cryptography.fernet import Fernet
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
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

def test_bff_session_store_create_rotate_and_revoke() -> None:
    from app.main import app as netpay_app

    session_hash = sha256(token_urlsafe(32).encode("ascii")).hexdigest()
    now = datetime.now(UTC)
    headers = {"X-NetPay-BFF-Secret": "test-internal-secret-value"}
    with TestClient(netpay_app) as client:
        ready = client.get("/internal/v1/bff/sessions/ready", headers=headers)
        assert ready.status_code == 200
        assert ready.json() == {"status": "ok"}

        created = client.post(
            "/internal/v1/bff/sessions",
            headers=headers,
            json={
                "session_id_hash": session_hash,
                "access_token": "access-token-one",
                "refresh_token": "refresh-token-one",
                "access_expires_at": (now + timedelta(minutes=30)).isoformat(),
                "expires_at": (now + timedelta(hours=2)).isoformat(),
            },
        )
        assert created.status_code == 201

        loaded = client.get("/internal/v1/bff/sessions/" + session_hash, headers=headers)
        assert loaded.status_code == 200
        assert loaded.json()["access_token"] == "access-token-one"
        assert loaded.json()["version"] == 1

        rotated = client.patch(
            "/internal/v1/bff/sessions/" + session_hash,
            headers=headers,
            json={
                "expected_version": 1,
                "access_token": "access-token-two",
                "refresh_token": "refresh-token-two",
                "access_expires_at": (now + timedelta(minutes=45)).isoformat(),
                "expires_at": (now + timedelta(hours=2)).isoformat(),
            },
        )
        assert rotated.status_code == 200
        assert rotated.json()["version"] == "2"

        stale_write = client.patch(
            "/internal/v1/bff/sessions/" + session_hash,
            headers=headers,
            json={
                "expected_version": 1,
                "access_token": "stale-token",
                "refresh_token": "stale-refresh",
                "access_expires_at": (now + timedelta(minutes=45)).isoformat(),
                "expires_at": (now + timedelta(hours=2)).isoformat(),
            },
        )
        assert stale_write.status_code == 409

        revoked = client.delete("/internal/v1/bff/sessions/" + session_hash, headers=headers)
        assert revoked.status_code == 204
        assert client.get("/internal/v1/bff/sessions/" + session_hash, headers=headers).status_code == 404
