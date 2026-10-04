"""Public SPA config — runtime OIDC bootstrap."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_config_json_public_and_unconfigured_by_default():
    from app.core.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/config.json")
    assert res.status_code == 200
    body = res.json()
    assert "oidc_issuer" in body
    assert "oidc_client_id" in body
    assert "oidc_configured" in body
    assert body["oidc_configured"] is False


@pytest.mark.asyncio
async def test_config_json_reflects_runtime_env(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", "https://auth.example.test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "spa-client-1")
    monkeypatch.setenv("OIDC_REDIRECT_URI", "https://pay.example.test/auth/callback")
    monkeypatch.setenv("OIDC_SCOPES", "openid profile email")

    from app.core.config import get_settings

    get_settings.cache_clear()
    # Re-import settings binding used by routes
    import app.core.config as config_mod
    import app.api.routes.health as health_mod

    config_mod.settings = get_settings()
    health_mod.settings = config_mod.settings

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/config.json")
    assert res.status_code == 200
    body = res.json()
    assert body["oidc_configured"] is True
    assert body["oidc_issuer"] == "https://auth.example.test"
    assert body["oidc_client_id"] == "spa-client-1"
    assert body["oidc_redirect_uri"] == "https://pay.example.test/auth/callback"
    assert "openid" in body["oidc_scopes"]

    get_settings.cache_clear()
