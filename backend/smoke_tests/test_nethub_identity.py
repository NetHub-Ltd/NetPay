"""Human identity via NetHubKe RS — forward Bearer, sync on 404, never verify JWT locally."""
from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.identity import nethub_client
from app.identity.nethub_client import NetHubIdentityError, fetch_me, resolve_human, sync_user
from app.identity.router import router as identity_router

USER_ID = str(uuid4())
USER_JSON = {
    "id": USER_ID,
    "email": "merchant@example.com",
    "full_name": "Example Merchant",
    "username": "merchant",
    "is_active": True,
    "is_admin": False,
    "tenant_id": None,
}


@pytest.fixture(autouse=True)
def _nethub_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETHUB_API_BASE_URL", "https://nethub.test")
    monkeypatch.setenv("NETHUB_API_TIMEOUT_SECONDS", "5")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def identity_client() -> TestClient:
    """Identity router only — no DB lifespan (M2M app startup needs Postgres)."""
    app = FastAPI()
    app.include_router(identity_router)
    return TestClient(app)


@pytest.mark.asyncio
async def test_fetch_me_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        assert method == "GET"
        assert path == "/api/v1/users/me"
        assert access_token == "idp-token"
        return httpx.Response(200, json=USER_JSON)

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    principal = await fetch_me("idp-token")
    assert principal.email == "merchant@example.com"
    assert str(principal.id) == USER_ID


@pytest.mark.asyncio
async def test_resolve_syncs_when_me_404(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        calls.append((method, path))
        if path == "/api/v1/users/me" and method == "GET":
            if calls.count(("GET", "/api/v1/users/me")) == 1:
                return httpx.Response(404, json={"detail": "not found"})
            return httpx.Response(200, json=USER_JSON)
        if path == "/api/v1/users/sync" and method == "POST":
            return httpx.Response(200, json=USER_JSON)
        return httpx.Response(500, json={"detail": "unexpected"})

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    principal = await resolve_human("idp-token")
    assert principal.email == "merchant@example.com"
    assert ("GET", "/api/v1/users/me") in calls
    assert ("POST", "/api/v1/users/sync") in calls


@pytest.mark.asyncio
async def test_fetch_me_401(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        return httpx.Response(401, json={"detail": "nope"})

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    with pytest.raises(NetHubIdentityError) as ei:
        await fetch_me("bad")
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_sync_503_on_upstream_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    with pytest.raises(NetHubIdentityError) as ei:
        await sync_user("tok")
    assert ei.value.status_code == 503


@pytest.mark.asyncio
async def test_missing_nethub_url_is_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETHUB_API_BASE_URL", "")
    get_settings.cache_clear()
    with pytest.raises(NetHubIdentityError) as ei:
        await fetch_me("tok")
    assert ei.value.status_code == 503


def test_auth_me_requires_bearer(identity_client: TestClient) -> None:
    response = identity_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "bearer_token_required"


def test_auth_me_success(identity_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.identity.principal import HumanPrincipal

    async def fake_resolve(token: str) -> HumanPrincipal:
        assert token == "idp-access"
        return HumanPrincipal(
            id=UUID(USER_ID),
            email="merchant@example.com",
            full_name="Example Merchant",
            username="merchant",
            is_active=True,
            is_admin=False,
            tenant_id=None,
        )

    monkeypatch.setattr("app.identity.deps.resolve_human", fake_resolve)
    response = identity_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer idp-access"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == "merchant@example.com"
    assert body["auth_type"] == "human_nethub"
    assert body["id"] == USER_ID


def test_auth_me_inactive_forbidden(identity_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.identity.principal import HumanPrincipal

    async def fake_resolve(token: str) -> HumanPrincipal:
        return HumanPrincipal(
            id=UUID(USER_ID),
            email="merchant@example.com",
            is_active=False,
        )

    monkeypatch.setattr("app.identity.deps.resolve_human", fake_resolve)
    response = identity_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer idp-access"},
    )
    assert response.status_code == 403
