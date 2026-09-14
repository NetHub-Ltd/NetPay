"""P1 #24 — C2B confirmation → canonical payment (M-Pesa payload is source of truth)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.helpers import internal_headers, login, seed_tenant_user_integration


@pytest.fixture
async def c2b_env(client: AsyncClient):
    seed_tenant_user_integration(
        slug="c2b-tenant",
        email="c2buser@nethub.test",
        public_id="gw_c2b_test_01",
    )
    token = await login(client, "c2buser@nethub.test", __import__("os").environ["TEST_USER_PASSWORD"])
    return {"token": token, "public_id": "gw_c2b_test_01"}


async def _open_intent(client: AsyncClient, env: dict, *, ref: str, amount_minor: int = 500) -> str:
    headers = {
        "Authorization": f"Bearer {env['token']}",
        "Idempotency-Key": f"c2b-open-{uuid4()}",
    }
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={
            "checkout_request_id": f"ws_c2b_{uuid4().hex[:8]}",
            "merchant_request_id": "mr_c2b",
        },
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="fixture-access-token",
    ):
        res = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": env["public_id"],
                "phone": "254700000001",
                "amount_minor": amount_minor,
                "account_reference": ref,
                "description": "C2B order",
            },
        )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _confirmation_envelope(public_id: str, *, bill_ref: str, trans_id: str, amount: str = "5.00"):
    return {
        "event_id": f"evt_c2b_{uuid4()}",
        "provider": "mpesa",
        "event_type": "c2b_confirmation",
        "integration": {"public_id": public_id},
        "payload": {
            "TransactionType": "Pay Bill",
            "TransID": trans_id,
            "TransTime": "20260914220000",
            "TransAmount": amount,
            "BusinessShortCode": "174379",
            "BillRefNumber": bill_ref,
            "MSISDN": "254700000001",
            "FirstName": "Test",
        },
    }


@pytest.mark.asyncio
async def test_c2b_confirmation_settles_open_intent(client: AsyncClient, c2b_env):
    ref = f"ORD{uuid4().hex[:6].upper()}"
    intent_id = await _open_intent(client, c2b_env, ref=ref, amount_minor=500)
    env = _confirmation_envelope(c2b_env["public_id"], bill_ref=ref, trans_id=f"NHL{uuid4().hex[:8].upper()}")
    r = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "succeeded"
    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {c2b_env['token']}"},
    )
    assert got.json()["status"] == "succeeded"
    assert got.json().get("provider_transaction_id")
    led = await client.get(
        f"/v1/payment-intents/{intent_id}/ledger",
        headers={"Authorization": f"Bearer {c2b_env['token']}"},
    )
    assert len(led.json()) == 1


@pytest.mark.asyncio
async def test_c2b_duplicate_trans_id_no_second_ledger(client: AsyncClient, c2b_env):
    ref = f"DUP{uuid4().hex[:6].upper()}"
    intent_id = await _open_intent(client, c2b_env, ref=ref, amount_minor=500)
    trans = f"NHL{uuid4().hex[:8].upper()}"
    env = _confirmation_envelope(c2b_env["public_id"], bill_ref=ref, trans_id=trans)
    r1 = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r1.json().get("status") == "succeeded"
    # Second confirmation same TransID
    env2 = _confirmation_envelope(c2b_env["public_id"], bill_ref=ref, trans_id=trans)
    env2["event_id"] = f"evt_c2b_dup_{uuid4()}"
    r2 = await client.post("/internal/events", json=env2, headers=internal_headers())
    assert r2.status_code == 200
    assert r2.json().get("status") in ("duplicate", "succeeded")  # terminal → duplicate
    led = await client.get(
        f"/v1/payment-intents/{intent_id}/ledger",
        headers={"Authorization": f"Bearer {c2b_env['token']}"},
    )
    assert len(led.json()) == 1


@pytest.mark.asyncio
async def test_c2b_unknown_bill_ref_unmatched(client: AsyncClient, c2b_env):
    env = _confirmation_envelope(
        c2b_env["public_id"],
        bill_ref="NOSUCHREF01",
        trans_id=f"NHL{uuid4().hex[:8].upper()}",
    )
    r = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "unmatched"


@pytest.mark.asyncio
async def test_c2b_missing_bill_ref_unmatched(client: AsyncClient, c2b_env):
    env = {
        "event_id": f"evt_nobill_{uuid4()}",
        "provider": "mpesa",
        "event_type": "c2b_confirmation",
        "integration": {"public_id": c2b_env["public_id"]},
        "payload": {
            "TransID": f"NHL{uuid4().hex[:8].upper()}",
            "TransAmount": "10.00",
            "MSISDN": "254700000002",
        },
    }
    r = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "unmatched"


@pytest.mark.asyncio
async def test_c2b_amount_mismatch_opens_exception(client: AsyncClient, c2b_env):
    ref = f"AMT{uuid4().hex[:6].upper()}"
    intent_id = await _open_intent(client, c2b_env, ref=ref, amount_minor=500)  # 5.00
    env = _confirmation_envelope(
        c2b_env["public_id"],
        bill_ref=ref,
        trans_id=f"NHL{uuid4().hex[:8].upper()}",
        amount="9.00",  # mismatch
    )
    r = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "amount_mismatch"
    got = await client.get(
        f"/v1/payment-intents/{intent_id}",
        headers={"Authorization": f"Bearer {c2b_env['token']}"},
    )
    # Must not silently succeed
    assert got.json()["status"] != "succeeded"


@pytest.mark.asyncio
async def test_c2b_validation_accepted(client: AsyncClient, c2b_env):
    env = {
        "event_id": f"evt_val_{uuid4()}",
        "provider": "mpesa",
        "event_type": "c2b_validation",
        "integration": {"public_id": c2b_env["public_id"]},
        "payload": {"BillRefNumber": "X", "TransAmount": "1.00"},
    }
    r = await client.post("/internal/events", json=env, headers=internal_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "accepted"
