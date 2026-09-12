"""P1-B reconciliation scan + resolve."""
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
        tenant = session.exec(select(Tenant).where(Tenant.slug == "p1b-tenant")).first()
        if not tenant:
            tenant = Tenant(name="P1B", slug="p1b-tenant", status="active", created_by=admin.id)
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
        integ = session.exec(select(Integration).where(Integration.public_id == "gw_p1b")).first()
        if not integ:
            integ = Integration(
                tenant_id=tenant.id,
                public_id="gw_p1b",
                shortcode="174379",
                type="paybill",
                environment="sandbox",
                status="active",
            )
            session.add(integ)
            session.commit()
            session.refresh(integ)
            for kind, val in [("consumer_key", "k"), ("consumer_secret", "s"), ("passkey", "p")]:
                session.add(Credential(integration_id=integ.id, kind=kind, value=val))
            session.commit()
    engine.dispose()
    return {"public_id": "gw_p1b"}


@pytest.fixture
async def admin_token(client: AsyncClient):
    _seed()
    res = await client.post(
        "/auth/login",
        json={"email": "admin@nethub.test", "password": "ChangeMeAdmin123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_scan_flags_succeeded_without_ledger(client: AsyncClient, admin_token):
    # Create + simulate success normally creates ledger; force a succeeded without ledger by
    # creating intent and manually marking succeeded in DB without ledger.
    headers = {"Authorization": f"Bearer {admin_token}", "Idempotency-Key": f"p1b-{uuid4()}"}
    with patch(
        "app.api.routes.payments.stk_push",
        new_callable=AsyncMock,
        return_value={"checkout_request_id": "ws_p1b_1", "merchant_request_id": "mr"},
    ), patch(
        "app.api.routes.payments.get_access_token",
        new_callable=AsyncMock,
        return_value="token",
    ):
        created = await client.post(
            "/v1/payment-intents",
            headers=headers,
            json={
                "integration_public_id": "gw_p1b",
                "phone": "254700999888",
                "amount_minor": 100,
            },
        )
        assert created.status_code == 201, created.text
        intent_id = created.json()["id"]

    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        intent = session.get(PaymentIntent, UUID(str(intent_id)))
        assert intent
        intent.status = "succeeded"
        intent.provider_transaction_id = "FORCED"
        session.add(intent)
        session.commit()
    engine.dispose()

    scan = await client.post(
        "/v1/reconciliation/scan",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert scan.status_code == 200, scan.text
    assert scan.json()["exceptions_created"] >= 1

    listing = await client.get(
        "/v1/reconciliation/exceptions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert listing.status_code == 200
    rows = listing.json()
    assert any(r["payment_intent_id"] == intent_id and r["kind"] == "unmatched_netpay" for r in rows)
    target = next(r for r in rows if r["payment_intent_id"] == intent_id)
    resolved = await client.post(
        f"/v1/reconciliation/exceptions/{target['id']}/resolve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"resolved_note": "Investigated in test"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
