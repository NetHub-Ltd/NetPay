"""P1-A: durable inbound events + expire stale intents."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.integration import Credential, Integration
from app.models.payment_intent import PaymentIntent
from app.models.tenant import Tenant
from app.models.user import User


def _seed():
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.email == "admin@nethub.test")).first()
        assert admin
        tenant = session.exec(select(Tenant).where(Tenant.slug == "p1-tenant")).first()
        if not tenant:
            tenant = Tenant(name="P1", slug="p1-tenant", status="active", created_by=admin.id)
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
        user = session.exec(select(User).where(User.email == "p1user@nethub.test")).first()
        if not user:
            user = User(
                email="p1user@nethub.test",
                hashed_password=hash_password("P1UserPass123!"),
                role="user",
                tenant_id=tenant.id,
                is_active=True,
            )
            session.add(user)
            session.commit()
        integ = session.exec(select(Integration).where(Integration.public_id == "gw_p1_test")).first()
        if not integ:
            integ = Integration(
                tenant_id=tenant.id,
                public_id="gw_p1_test",
                shortcode="174379",
                type="paybill",
                environment="sandbox",
                status="active",
            )
            session.add(integ)
            session.commit()
            session.refresh(integ)
            for kind, val in [
                ("consumer_key", "k"),
                ("consumer_secret", "s"),
                ("passkey", "p"),
            ]:
                session.add(Credential(integration_id=integ.id, kind=kind, value=val))
            session.commit()
        out = {"public_id": "gw_p1_test"}
    engine.dispose()
    return out


async def _login(client: AsyncClient) -> str:
    res = await client.post(
        "/auth/login", json={"email": "p1user@nethub.test", "password": "P1UserPass123!"}
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
async def p1_env(client: AsyncClient):
    meta = _seed()
    token = await _login(client)
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
        return_value="token",
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
    h = {"X-Internal-Api-Key": "test-internal-key"}
    r1 = await client.post("/internal/events", json=envelope, headers=h)
    assert r1.status_code == 200
    assert r1.json().get("status") == "succeeded"
    r2 = await client.post("/internal/events", json=envelope, headers=h)
    assert r2.status_code == 200
    # Cached processed result (not a second business apply)
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
        return_value="token",
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

    # Backdate updated_at so it looks stale
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        intent = session.get(PaymentIntent, UUID(str(intent_id)))
        assert intent is not None
        intent.updated_at = datetime.now(timezone.utc) - timedelta(seconds=10_000)
        session.add(intent)
        session.commit()
    engine.dispose()

    res = await client.post(
        "/internal/expire-stale",
        headers={"X-Internal-Api-Key": "test-internal-key"},
    )
    assert res.status_code == 200, res.text
    assert res.json().get("expired", 0) >= 1

    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p1_env['token']}"},
    )
    assert got.json()["status"] == "expired"

    # Late success callback must not revive
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
    late = await client.post(
        "/internal/events",
        json=envelope,
        headers={"X-Internal-Api-Key": "test-internal-key"},
    )
    assert late.status_code == 200
    assert late.json().get("status") == "ignored"
    got2 = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p1_env['token']}"},
    )
    assert got2.json()["status"] == "expired"
