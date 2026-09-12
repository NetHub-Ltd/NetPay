"""P0 financial integrity: idempotency, double callback, tenant isolation, ledger."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from tests.helpers import (
    FIXTURE_USER_PASSWORD,
    internal_headers,
    login,
    seed_tenant_user_integration,
)


def _seed_other_tenant() -> None:
    """Second tenant for isolation tests."""
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.email == "admin@nethub.test")).first()
        assert admin
        other = session.exec(select(Tenant).where(Tenant.slug == "p0-other")).first()
        if not other:
            other = Tenant(name="Other", slug="p0-other", status="active", created_by=admin.id)
            session.add(other)
            session.commit()
            session.refresh(other)
            session.add(
                User(
                    email="p0other@nethub.test",
                    hashed_password=hash_password(FIXTURE_USER_PASSWORD),
                    role="user",
                    tenant_id=other.id,
                    is_active=True,
                )
            )
            session.commit()
    engine.dispose()


@pytest.fixture
async def p0_env(client: AsyncClient):
    meta = seed_tenant_user_integration(
        slug="p0-tenant",
        email="p0user@nethub.test",
        public_id="gw_p0_test",
    )
    _seed_other_tenant()
    token = await login(client, meta["email"], FIXTURE_USER_PASSWORD)
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
        return_value={"checkout_request_id": "ws_checkout_1", "merchant_request_id": "mr_1"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
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
        return {"checkout_request_id": f"ws_conc_{call_count['n']}", "merchant_request_id": "mr_c"}

    with patch("app.api.routes.payments.stk_push", side_effect=fake_stk), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
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
        if r.status_code == 201:
            bodies.append(r.json())
    assert len(bodies) >= 1
    assert len({b["id"] for b in bodies}) == 1


@pytest.mark.asyncio
async def test_double_callback_one_succeeded(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": "idem-callback-1",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_double_cb", "merchant_request_id": "mr_d"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
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
    r1 = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r1.status_code == 200
    assert r1.json().get("status") == "succeeded"
    envelope["event_id"] = "evt_dup_2"
    r2 = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r2.status_code == 200
    assert r2.json().get("status") == "duplicate"

    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {p0_env['token']}"},
    )
    assert got.status_code == 200
    assert got.json()["status"] == "succeeded"


@pytest.mark.asyncio
async def test_tenant_isolation_forbidden(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": f"idem-iso-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_iso_1", "merchant_request_id": "mr_i"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
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

    other_token = await login(client, "p0other@nethub.test", FIXTURE_USER_PASSWORD)
    res = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_ledger_one_credit_on_success_and_duplicate_callback(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": f"idem-ledger-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_ledger_1", "merchant_request_id": "mr_l"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p0_env["public_id"],
                "phone": "254733333333",
                "amount_minor": 500,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    envelope = {
        "event_id": "evt_led_1",
        "provider": "mpesa",
        "event_type": "stk.callback",
        "integration": {"public_id": p0_env["public_id"]},
        "payload": {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_ledger_1",
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {
                        "Item": [{"Name": "MpesaReceiptNumber", "Value": "LEDGER1"}]
                    },
                }
            }
        },
    }
    r1 = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r1.status_code == 200
    envelope["event_id"] = "evt_led_2"
    await client.post("/internal/events", json=envelope, headers=internal_headers())

    led = await client.get(
        f"/v1/payment-intents/{intent_id}/ledger",
        headers={"Authorization": f"Bearer {p0_env['token']}"},
    )
    assert led.status_code == 200, led.text
    rows = led.json()
    assert len(rows) == 1
    assert rows[0]["entry_type"] == "collection_credit"
    assert rows[0]["amount_minor"] == 500


@pytest.mark.asyncio
async def test_failed_intent_has_no_ledger_credit(client: AsyncClient, p0_env):
    headers = {
        "Authorization": f"Bearer {p0_env['token']}",
        "Idempotency-Key": f"idem-fail-led-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_fail_led", "merchant_request_id": "mr_f"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": p0_env["public_id"],
                "phone": "254744444444",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    envelope = {
        "event_id": "evt_fail_1",
        "provider": "mpesa",
        "event_type": "stk.callback",
        "integration": {"public_id": p0_env["public_id"]},
        "payload": {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_fail_led",
                    "ResultCode": 1032,
                    "ResultDesc": "Cancelled by user",
                }
            }
        },
    }
    r = await client.post("/internal/events", json=envelope, headers=internal_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "failed"
    led = await client.get(
        f"/v1/payment-intents/{intent_id}/ledger",
        headers={"Authorization": f"Bearer {p0_env['token']}"},
    )
    assert led.status_code == 200
    assert led.json() == []
