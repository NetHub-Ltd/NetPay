"""Rate limit fails closed when Redis is required and unavailable."""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core import rate_limit as rl


def _dummy_request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/oauth/token",
        "raw_path": b"/v1/oauth/token",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_rate_limit_503_when_redis_required(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "redis_required", True)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "rate_limit_token_per_minute", 10)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    async def no_redis(*_a, **_k):
        return None

    monkeypatch.setattr(rl, "_redis_hit", no_redis)

    with pytest.raises(HTTPException) as ei:
        await rl.enforce_rate_limit(_dummy_request(), bucket="oauth_token", limit=10)
    assert ei.value.status_code == 503
    assert ei.value.detail == "rate_limit_unavailable"


@pytest.mark.asyncio
async def test_rate_limit_memory_when_redis_optional(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "redis_required", False)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    rl._buckets.clear()

    async def no_redis(*_a, **_k):
        return None

    monkeypatch.setattr(rl, "_redis_hit", no_redis)

    # Should not raise 503 — memory path allows first requests
    await rl.enforce_rate_limit(_dummy_request(), bucket="oauth_token", limit=5, identity="t1")
