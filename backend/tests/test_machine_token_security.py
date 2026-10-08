"""Machine token audience, TTL, and rate-limit behaviour."""
from __future__ import annotations

from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import create_machine_token, create_access_token, decode_token


@pytest.mark.asyncio
async def test_machine_token_includes_aud_and_typ():
    token = create_machine_token(
        subject="cli_test",
        extra={"client_id": "cli_test", "tenant_id": str(uuid4()), "name": "t"},
    )
    payload = decode_token(token)
    assert payload.get("typ") == "machine"
    assert payload.get("aud") == settings.machine_token_audience


@pytest.mark.asyncio
async def test_machine_principal_rejects_missing_aud(client):
    """Token without aud must not authenticate as machine."""
    from app.api.deps import _try_machine_principal

    # Legacy-style token (no aud) — should be rejected by principal resolver
    token = create_access_token(
        subject="cli_legacy",
        extra={
            "typ": "machine",
            "client_id": "cli_legacy",
            "tenant_id": str(uuid4()),
            "name": "legacy",
        },
    )
    assert _try_machine_principal(token) is None


@pytest.mark.asyncio
async def test_machine_principal_accepts_valid_aud():
    from app.api.deps import _try_machine_principal

    tid = uuid4()
    token = create_machine_token(
        subject="cli_ok",
        extra={"client_id": "cli_ok", "tenant_id": str(tid), "name": "ok"},
    )
    principal = _try_machine_principal(token)
    assert principal is not None
    assert principal.client_id == "cli_ok"
    assert principal.tenant_id == tid


@pytest.mark.asyncio
async def test_openapi_disabled_in_production_config():
    from app.core.config import Settings

    s = Settings(environment="production", openapi_enabled=None)
    assert s.openapi_enabled_effective is False
    s2 = Settings(environment="development", openapi_enabled=None)
    assert s2.openapi_enabled_effective is True
    s3 = Settings(environment="production", openapi_enabled=True)
    assert s3.openapi_enabled_effective is True


@pytest.mark.asyncio
async def test_production_secret_guard():
    from app.core.config import Settings

    s = Settings(environment="production", secret_key="dev-secret-change-me")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        s.assert_production_secrets()
    s_ok = Settings(
        environment="production",
        secret_key="a-strong-production-secret-key-32b",
        internal_api_key="a-strong-internal-key-32bytes-xx",
    )
    s_ok.assert_production_secrets()  # must not raise


@pytest.mark.asyncio
async def test_token_rate_limit_returns_429(client, monkeypatch):
    """With a very low limit, repeated token attempts should 429."""
    from app.core import rate_limit as rl
    from app.core.config import settings as cfg

    monkeypatch.setattr(cfg, "rate_limit_token_per_minute", 2)
    monkeypatch.setattr(cfg, "rate_limit_window_seconds", 60)
    # clear memory buckets
    rl._buckets.clear()

    body = {
        "grant_type": "client_credentials",
        "client_id": "cli_nonexistent",
        "client_secret": "wrong-secret-value",
    }
    # First two may 401 (invalid client) but must not 429; third should 429
    statuses = []
    for _ in range(3):
        res = await client.post("/v1/oauth/token", json=body)
        statuses.append(res.status_code)
    assert 429 in statuses, statuses
