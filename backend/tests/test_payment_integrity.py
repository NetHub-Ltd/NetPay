"""P0 financial integrity: idempotency, double callback, tenant isolation."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import Session, select
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.integration import Credential, Integration
from app.models.tenant import Tenant
from app.models.user import User


def _sync_seed():
    """Seed tenant, integration, credentials, tenant user via sync engine."""
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.email == "admin@nethub.test")).first()
        assert admin is not None
        tenant = session.exec(select(Tenant).where(Tenant.slug == "p0-tenant")).first()
        if not tenant:
            tenant = Tenant(name="P0 Tenant", slug="p0-tenant", status="active", created_by=admin.id)
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
        user = session.exec(select(User).where(User.email == "p0user@nethub.test")).first()
        if not user:
            user = User(
                email="p0user@nethub.test",
                hashed_password=hash_password("P0UserPass123!"),
                display_name="P0 User",
                role="user",
                tenant_id=tenant.id,
                is_active=True,
            )
            session.add(user)
            session.commit()
        other = session.exec(select(User).where(User.email == "p0other@nethub.test")).first()
        if not other:
            other_tenant = Tenant(
                name="Other Tenant", slug="p0-other", status="active", created_by=admin.id
            )
            session.add(other_tenant)
            session.commit()
            session.refresh(other_tenant)
            other = User(
                email="p0other@nethub.test",
                hashed_password=hash_password("P0OtherPass123!"),
                role="user",
                tenant_id=other_tenant.id,
                is_active=True,
            )
            session.add(other)
            session.commit()
        integ = session.exec(
            select(Integration).where(Integration.public_id == "gw_p0_test")
        ).first()
        if not integ:
            integ = Integration(
                tenant_id=tenant.id,
                public_id="gw_p0_test",
                shortcode="174379",
                type="paybill",
                environment="sandbox",
                status="active",
            )
            session.add(integ)
            session.commit()
            session.refresh(integ)
            for kind, val in [
                ("consumer_key", "test_key"),
                ("consumer_secret", "test_secret"),
                ("passkey", "test_passkey"),
            ]:
                session.add(Credential(integration_id=integ.id, kind=kind, value=val))
            session.commit()
        out = {
            "tenant_id": str(tenant.id),
            "public_id": "gw_p0_test",
        }
    engine.dispose()
    return out


async def _login(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
async def p0_env(client: AsyncClient):
    meta = _sync_seed()
    token = await _login(client, "p0user@nethub.test", "P0UserPass123!")
    return {**meta, "token": token}


@pytest.mark.asyncio
async def test_create_requires_idempotency_key(client: AsyncClient, p0_env):
    res = await client.post(
        "/v1/payment-intents",
        headers={"Authorization": f"Bearer {p0_env['token']}"},
        json={
            "integration_public_id": p0_env["public_id"],
            "phone": "254712345678",
            "amount_minor": 100,
        },
    )
    assert res.status_code == 400
    assert "Idempotency-Key" in res.json()["detail"]


@pytest.mark.asyncio
async def test_idempotent_replay_same_key(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": "idem-replay-1",
    }
    body = {
        "integration_public_id": p0_env["public_id"],
        "phone": "254712345678",
        "amount_minor": 100,
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={
            "checkout_request_id": "ws_checkout_1",
            "merchant_request_id": "mr_1",
        },
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="token",
    ):
        r1 = await client.post("/v1/payment-intents", headers=headers, json=body)
        assert r1.status_code == 201, r1.text
        d1 = r1.json()
        assert d1["idempotent_replay"] is False
        assert d1["amount_minor"] == 100
        assert d1["status"] == "provider_requested"

        r2 = await client.post("/v1/payment-intents", headers=headers, json=body)
        assert r2.status_code == 201, r2.text
        d2 = r2.json()
        assert d2["idempotent_replay"] is True
        assert d2["id"] == d1["id"]
        assert d2["provider_checkout_id"] == d1["provider_checkout_id"]


@pytest.mark.asyncio
async def test_concurrent_idempotency_one_intent(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": "idem-concurrent-1",
    }
    body = {
        "integration_public_id": p0_env["public_id"],
        "phone": "254700000001",
        "amount_minor": 200,
    }
    call_count = {"n": 0}

    async def fake_stk(**kwargs):
        call_count["n"] += 1
        await asyncio.sleep(0.05)
        return {
            "checkout_request_id": f"ws_conc_{call_count['n']}",
            "merchant_request_id": "mr_c",
        }

    with patch("app.api.routes.payments.stk_push", side_effect=fake_stk), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="token",
    ):
        results = await asyncio.gather(
            client.post("/v1/payment-intents", headers=headers, json=body),
            client.post("/v1/payment-intents", headers=headers, json=body),
            return_exceptions=True,
        )
    bodies = []
    for r in results:
        if isinstance(r, Exception):
            continue
        assert r.status_code in (201, 400, 409, 500), getattr(r, "text", r)
        if r.status_code == 201:
            bodies.append(r.json())
    assert len(bodies) >= 1
    ids = {b["id"] for b in bodies}
    # Same idempotency key must not yield two different successful intent ids
    assert len(ids) == 1


@pytest.mark.asyncio
async def test_double_callback_one_succeeded(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": "idem-callback-1",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={
            "checkout_request_id": "ws_double_cb",
            "merchant_request_id": "mr_d",
        },
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p0_env["public_id"],
                "phone": "254711111111",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    envelope = {
        "event_id": "evt_dup_1",
        "provider": "mpesa",
        "event_type": "stk.callback",
        "integration": {"public_id": p0_env["public_id"]},
        "payload": {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_double_cb",
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {
                        "Item": [{"Name": "MpesaReceiptNumber", "Value": "ABC123"}]
                    },
                }
            }
        },
    }
    h = {"X-Internal-Api-Key": "test-internal-key"}
    r1 = await client.post("/internal/events", json=envelope, headers=h)
    assert r1.status_code == 200, r1.text
    assert r1.json().get("status") == "succeeded"
    envelope["event_id"] = "evt_dup_2"
    r2 = await client.post("/internal/events", json=envelope, headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json().get("status") == "duplicate"

    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p0_env['token']}"},
    )
    assert got.status_code == 200
    assert got.json()["status"] == "succeeded"
    assert got.json()["provider_transaction_id"] == "ABC123"


@pytest.mark.asyncio
async def test_tenant_isolation_forbidden(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": f"idem-iso-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={
            "checkout_request_id": "ws_iso_1",
            "merchant_request_id": "mr_i",
        },
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p0_env["public_id"],
                "phone": "254722222222",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    other_token = await _login(client, "p0other@nethub.test", "P0OtherPass123!")
    res = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 403
