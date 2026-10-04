"""Workspace readiness endpoint."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_readiness_requires_auth():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/v1/readiness")
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_readiness_shape_for_admin(client):
    res = await client.get("/v1/readiness")
    assert res.status_code == 200
    body = res.json()
    assert "ready_to_collect" in body
    assert "next_step" in body
    assert "has_shortcode" in body
    assert "has_connected_shortcode" in body
