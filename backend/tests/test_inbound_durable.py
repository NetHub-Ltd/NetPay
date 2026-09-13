"""P1-A: durable inbound events + expire stale intents."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app.core.config import settings
from app.models.payment_intent import PaymentIntent
from tests.helpers import FIXTURE_USER_PASSWORD, internal_headers, login, seed_tenant_user_integration


@pytest.fixture
async def p1_env(client: AsyncClient):
    meta = seed_tenant_user_integration(
        slug="p1-tenant",
        email="p1user@nethub.test",
        public_id="gw_p1_test",
    )
    token = await login(client, meta["email"], FIXTURE_USER_PASSWORD)
    return {**meta, "token": token}


@pytest.mark.asyncio
async def test_duplicate_event_id_does_not_reprocess(client: AsyncClient, p1_env):
    headers = {
        "Authorization": f"Bearer {p1_env['token']}",
        "Idempotency-Key": f"p1-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_p1_dup", "merchant_request_id": "mr"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p1_env["public_id"],
                "phone": "254700111222",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text

    envelope = {
        "event_id": "evt_stable_1",
        "provider": "mpesa",
        "event_type": "stk.callback",
        "integration": {"public_id": p1_env["public_id"]},
        "payload": {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_p1_dup",
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {
                        "Item": [{"Name": "MpesaReceiptNumber", "Value": "RCPT1"}]
                    },
                }
            }
        },
    }
    r1 = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r1.status_code == 200
    assert r1.json().get("status") == "succeeded"
    r2 = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r2.status_code == 200
    assert r2.json().get("status") == "succeeded"


@pytest.mark.asyncio
async def test_expire_stale_provider_requested(client: AsyncClient, p1_env):
    headers = {
        "Authorization": f"Bearer {p1_env['token']}",
        "Idempotency-Key": f"p1-exp-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_p1_exp", "merchant_request_id": "mr"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p1_env["public_id"],
                "phone": "254700333444",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        intent = session.get(PaymentIntent, UUID(str(intent_id)))
        assert intent is not None
        intent.updated_at = datetime.now(timezone.utc) - timedelta(seconds=10_000)
        session.add(intent)
        session.commit()
    engine.dispose()

    res = await client.post("/internal/expire-stale", headers=internal_headers())
    assert res.status_code == 200, res.text
    assert res.json().get("expired", 0) >= 1

    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p1_env['token']}"},
    )
    assert got.json()["status"] == "expired"

    envelope = {
        "event_id": f"evt_late_{uuid4()}",
        "provider": "mpesa",
        "event_type": "stk.callback",
        "integration": {"public_id": p1_env["public_id"]},
        "payload": {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_p1_exp",
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                }
            }
        },
    }
    late = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert late.status_code == 200
    assert late.json().get("status") == "ignored"
    got2 = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p1_env['token']}"},
    )
    assert got2.json()["status"] == "expired"


@pytest.mark.asyncio
async def test_edge_heartbeat_accepted(client: AsyncClient):
    envelope = {
        "event_id": f"hb_test_{uuid4()}",
        "provider": "mpesa",
        "event_type": "edge.heartbeat",
        "integration": {"public_id": "gw_heartbeat"},
        "payload": {"source": "test"},
    }
    r = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") in ("ok", "succeeded")
    # Status endpoint requires auth — admin from bootstrap
    from tests.helpers import login_admin
    token = await login_admin(client)
    st = await client.get(
        "/v1/system/edge-connection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert st.status_code == 200, st.text
    data = st.json()
    assert data.get("last_inbound_at") is not None
    assert data.get("last_heartbeat_at") is not None
