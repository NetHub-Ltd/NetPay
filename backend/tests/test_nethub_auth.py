from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from app.core.config import get_settings, settings
from app.services import nethub_auth
from app.services.nethub_auth import NetHubAuthError, fetch_principal


@pytest.fixture
def nethub_base(monkeypatch):
    monkeypatch.setattr(settings, "nethub_api_base_url", "https://nethub.test")
    monkeypatch.setattr(settings, "admin_email", "admin@nethub.test")
    yield


@pytest.mark.asyncio
async def test_fetch_principal_ok(nethub_base, monkeypatch):
    uid = uuid4()
    tid = uuid4()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/api/v1/users/me")
        assert request.headers.get("Authorization") == "Bearer tok"
        return httpx.Response(
            200,
            json={
                "id": str(uid),
                "email": "a@b.co",
                "full_name": "A",
                "username": "a",
                "is_active": True,
                "tenant_id": str(tid),
                "tenant_name": "T",
                "tenant_tier": "free",
            },
        )

    transport = httpx.MockTransport(handler)

    class FakeClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(nethub_auth.httpx, "AsyncClient", FakeClient)
    p = await fetch_principal("tok")
    assert p.id == uid
    assert p.email == "a@b.co"
    assert p.tenant_id == tid


@pytest.mark.asyncio
async def test_fetch_principal_unauthorized(nethub_base, monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    transport = httpx.MockTransport(handler)

    class FakeClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(nethub_auth.httpx, "AsyncClient", FakeClient)
    with pytest.raises(NetHubAuthError) as ei:
        await fetch_principal("bad")
    assert ei.value.status_code == 401
