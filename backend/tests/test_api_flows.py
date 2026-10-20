from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlmodel import Session

import pytest

from app.config import get_settings
from app.crypto import encrypt_secret
from app.daraja.stk import STKAccepted
from app.main import app
from app.models import DarajaIntegration, EventOutbox, M2MClient, Merchant, Payment
from app.security import create_access_token, hash_client_secret


CLIENT_SECRET = "integration-test-client-secret-that-is-long-enough"
pytestmark = pytest.mark.skipif(get_settings().environment != "test", reason="API integration tests require ENVIRONMENT=test")


def _sync_url() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)


def _seed_client(scopes: list[str]) -> tuple[UUID, str]:
    engine = create_engine(_sync_url())
    now = datetime.now(timezone.utc)
    merchant = Merchant(name=f"Test merchant {uuid4()}", status="active", created_at=now, updated_at=now)
    client = M2MClient(
        merchant_id=merchant.id,
        client_id=f"test_{uuid4().hex}",
        secret_hash=hash_client_secret(CLIENT_SECRET),
        scopes=scopes,
        status="active",
        created_at=now,
    )
    merchant_id = merchant.id
    client_id = client.client_id
    with Session(engine) as session:
        session.add(merchant)
        session.add(client)
        session.commit()
    token, _ = create_access_token(client_id, merchant_id, scopes)
    engine.dispose()
    return merchant_id, token


def _seed_integration(merchant_id: UUID) -> str:
    engine = create_engine(_sync_url())
    settings = get_settings()
    now = datetime.now(timezone.utc)
    integration_id = f"int_{uuid4().hex}"
    integration = DarajaIntegration(
        integration_id=integration_id,
        merchant_id=merchant_id,
        environment="sandbox",
        shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        consumer_key_ciphertext=encrypt_secret("consumer-key", settings),
        consumer_secret_ciphertext=encrypt_secret("consumer-secret", settings),
        passkey_ciphertext=encrypt_secret("passkey", settings),
        credential_status="oauth_validated",
        c2b_enabled=False,
        c2b_registration_status="not_requested",
        stk_callback_url=f"https://gateway.example.test/cb/stk/{integration_id}",
        c2b_validation_url=f"https://gateway.example.test/cb/c2b/validation/{integration_id}",
        c2b_confirmation_url=f"https://gateway.example.test/cb/c2b/confirmation/{integration_id}",
        created_at=now,
        updated_at=now,
    )
    with Session(engine) as session:
        session.add(integration)
        session.commit()
    engine.dispose()
    return integration_id


def test_integration_creation_never_returns_provider_secrets(monkeypatch) -> None:
    _merchant_id, token = _seed_client(["integrations:read", "integrations:write"])

    async def fake_token(*args, **kwargs) -> str:
        return "temporary-token"

    monkeypatch.setattr("app.routers.integrations.request_access_token", fake_token)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/integrations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "environment": "sandbox",
                "shortcode": "600001",
                "product_type": "paybill",
                "consumer_key": "consumer-key-secret",
                "consumer_secret": "consumer-secret-sensitive",
                "passkey": "passkey-sensitive",
            },
        )

    assert response.status_code == 201, response.text
    assert response.json()["credential_status"] == "oauth_validated"
    assert response.json()["c2b_registration_status"] == "not_requested"
    assert "consumer-secret-sensitive" not in response.text
    assert "passkey-sensitive" not in response.text


def test_cross_merchant_integration_lookup_is_denied() -> None:
    owner_id, _ = _seed_client(["integrations:read"])
    _, attacker_token = _seed_client(["integrations:read"])
    integration_id = _seed_integration(owner_id)

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/integrations/{integration_id}",
            headers={"Authorization": f"Bearer {attacker_token}"},
        )

    assert response.status_code == 404


def test_stk_idempotency_and_callback_are_durable(monkeypatch) -> None:
    merchant_id, token = _seed_client(["payments:read", "payments:write"])
    integration_id = _seed_integration(merchant_id)
    calls = 0

    async def fake_stk(**kwargs) -> STKAccepted:
        nonlocal calls
        calls += 1
        return STKAccepted(
            merchant_request_id="merchant-request-test",
            checkout_request_id="checkout-request-test",
            response_description="Request accepted for processing",
        )

    monkeypatch.setattr("app.routers.payments.initiate_stk_push", fake_stk)
    request_body = {
        "integration_id": integration_id,
        "client_reference": "order-123",
        "amount_minor": 2500,
        "currency": "KES",
        "phone_number": "0712345678",
        "description": "Test payment",
    }
    auth = {"Authorization": f"Bearer {token}"}
    with TestClient(app) as client:
        first = client.post("/api/v1/payments/stk-push", headers={**auth, "Idempotency-Key": "payment-key-0001"}, json=request_body)
        second = client.post("/api/v1/payments/stk-push", headers={**auth, "Idempotency-Key": "payment-key-0001"}, json=request_body)
        conflicting = client.post(
            "/api/v1/payments/stk-push",
            headers={**auth, "Idempotency-Key": "payment-key-0001"},
            json={**request_body, "amount_minor": 3500},
        )
        assert first.status_code == 202, first.text
        assert second.status_code == 202, second.text
        assert first.json()["id"] == second.json()["id"]
        assert first.json()["status"] == "pending"
        assert conflicting.status_code == 409
        payment_id = first.json()["id"]
        payment_uuid = UUID(payment_id)
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "merchant-request-test",
                    "CheckoutRequestID": "checkout-request-test",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 25.0},
                            {"Name": "MpesaReceiptNumber", "Value": "TESTRECEIPT123"},
                            {"Name": "TransactionDate", "Value": 20261020120000},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    },
                }
            }
        }
        callback_url = f"/cb/stk/{integration_id}"
        callback_first = client.post(callback_url, json=callback_payload)
        callback_second = client.post(callback_url, json=callback_payload)
        status_response = client.get(f"/api/v1/payments/{payment_id}", headers=auth)

    assert calls == 1
    assert callback_first.status_code == 200
    assert callback_second.status_code == 200
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "succeeded"
    assert status_response.json()["provider_receipt"] == "TESTRECEIPT123"

    engine = create_engine(_sync_url())
    with Session(engine) as session:
        payment_rows = session.exec(select(Payment).where(Payment.id == payment_uuid)).all()
        events = session.exec(select(EventOutbox).where(EventOutbox.aggregate_id == payment_uuid)).all()
    engine.dispose()
    assert len(payment_rows) == 1
    assert len(events) == 2
