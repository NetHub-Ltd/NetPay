from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers import internal_headers


@pytest.mark.asyncio
async def test_health_reports_db_and_admin(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in ("ok", "degraded")
    assert body.get("database") is True
    assert body.get("admin_ready") is True


@pytest.mark.asyncio
async def test_auth_me_via_nethub_principal(client: AsyncClient):
    """Dependency override supplies principal; /auth/me no longer uses password login."""
    res = await client.get("/auth/me", headers={"Authorization": "Bearer test"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("email") == "admin@nethub.test"
    assert body.get("role") == "admin"


@pytest.mark.asyncio
async def test_worker_path_rejects_missing_internal_key(client: AsyncClient):
    res = await client.post(
        "/internal/events",
        json={
            "event_id": "evt_1",
            "provider": "mpesa",
            "event_type": "stk.callback",
            "integration": {"public_id": "gw_test"},
            "payload": {},
        },
    )
    assert res.status_code == 401
