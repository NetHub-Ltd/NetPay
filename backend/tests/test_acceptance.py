from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers import ADMIN_EMAIL, ADMIN_PASSWORD, internal_headers


@pytest.mark.asyncio
async def test_health_reports_db_and_admin(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in ("ok", "degraded")
    assert body.get("database") is True
    assert body.get("admin_ready") is True


@pytest.mark.asyncio
async def test_admin_login_from_env_bootstrap(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    assert "access_token" in res.json()


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


@pytest.mark.asyncio
async def test_worker_path_rejects_wrong_internal_key(client: AsyncClient):
    res = await client.post(
        "/internal/events",
        json={
            "event_id": "evt_2",
            "provider": "mpesa",
            "event_type": "stk.callback",
            "integration": {"public_id": "gw_test"},
            "payload": {},
        },
        headers={"X-Internal-Api-Key": "wrong-key-not-configured"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_worker_path_accepts_valid_key(client: AsyncClient):
    res = await client.post(
        "/internal/events",
        json={
            "event_id": "evt_3",
            "provider": "mpesa",
            "event_type": "stk.callback",
            "integration": {"public_id": "gw_test"},
            "payload": {"Body": {"stkCallback": {"CheckoutRequestID": "ws_x", "ResultCode": 0}}},
        },
        headers=internal_headers(),
    )
    assert res.status_code != 401


@pytest.mark.asyncio
async def test_protected_routes_require_jwt(client: AsyncClient):
    res = await client.get("/v1/payment-intents")
    assert res.status_code == 401
