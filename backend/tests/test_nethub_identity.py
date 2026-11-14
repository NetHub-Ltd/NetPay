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


@pytest.mark.asyncio
async def test_resolve_human_cache_hit_skips_http(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.identity.principal import HumanPrincipal

    principal = HumanPrincipal(
        id=UUID(USER_ID),
        email="merchant@example.com",
        full_name="Example Merchant",
        username="merchant",
    )
    calls: list[tuple[str, str]] = []

    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        calls.append((method, path))
        return httpx.Response(200, json=USER_JSON)

    async def fake_cache_get(token: str) -> HumanPrincipal | None:
        assert token == "idp-token"
        return principal

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    monkeypatch.setattr(nethub_client, "_cache_get", fake_cache_get)

    result = await resolve_human("idp-token")
    assert result.email == "merchant@example.com"
    assert calls == []


@pytest.mark.asyncio
async def test_resolve_human_cache_miss_sets_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.identity.principal import HumanPrincipal

    stored: dict[str, HumanPrincipal] = {}

    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        assert path == "/api/v1/users/me"
        return httpx.Response(200, json=USER_JSON)

    async def fake_cache_get(token: str) -> HumanPrincipal | None:
        return stored.get(token)

    async def fake_cache_set(token: str, principal: HumanPrincipal) -> None:
        stored[token] = principal

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    monkeypatch.setattr(nethub_client, "_cache_get", fake_cache_get)
    monkeypatch.setattr(nethub_client, "_cache_set", fake_cache_set)

    first = await resolve_human("idp-token")
    assert first.email == "merchant@example.com"
    assert "idp-token" in stored

    # Second resolve should hit cache (no HTTP if we clear request)
    async def boom(method: str, path: str, access_token: str) -> httpx.Response:
        raise AssertionError("HTTP should not run on cache hit")

    monkeypatch.setattr(nethub_client, "_request", boom)
    second = await resolve_human("idp-token")
    assert second.email == first.email


@pytest.mark.asyncio
async def test_resolve_human_does_not_cache_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    sets: list[str] = []

    async def fake_request(method: str, path: str, access_token: str) -> httpx.Response:
        return httpx.Response(401, json={"detail": "nope"})

    async def fake_cache_get(token: str) -> None:
        return None

    async def fake_cache_set(token: str, principal: object) -> None:
        sets.append(token)

    monkeypatch.setattr(nethub_client, "_request", fake_request)
    monkeypatch.setattr(nethub_client, "_cache_get", fake_cache_get)
    monkeypatch.setattr(nethub_client, "_cache_set", fake_cache_set)

    with pytest.raises(NetHubIdentityError) as excinfo:
        await resolve_human("bad-token")
    assert excinfo.value.status_code == 401
    assert sets == []


@pytest.mark.asyncio
async def test_cache_get_redis_failure_degrades(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_ENABLED", "true")
    monkeypatch.setenv("NETHUB_USER_CACHE_TTL_SECONDS", "45")
    get_settings.cache_clear()

    def boom_client(settings: object) -> object:
        raise RuntimeError("redis down")

    monkeypatch.setattr("app.core.cache.create_redis_client", boom_client)
    assert await nethub_client._cache_get("any-token") is None
