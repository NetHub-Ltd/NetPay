"""Application-level payment lifecycle integration tests against PostgreSQL."""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete
from sqlmodel import Session as SyncSession, create_engine, select

from app import main as main_module
from app.core.config import Settings
from app.models.attempts import PaymentAttempt
from app.models.events import EventOutbox
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient, Merchant
from app.models.operations import AuditLog, ProviderRequest
from app.models.payments import IdempotencyRecord, Payment, ProviderCallback
from app.mpesa_core.credentials import decrypt_credentials, encrypt_credentials
from app.mpesa_core.errors import AmbiguousOutcome, OAuthError, OperationOutcome, ProviderRejected, RetryDisposition
from app.mpesa_core.schemas import ProviderOperationResult
from app.payments import router as router_module
from app.payments import security
from app.mpesa_core import credentials as core_credentials


def test_client_secret_hash_is_one_way_and_verified() -> None:
    """Provisioned client secrets validate without being stored in plaintext."""
    secret = "high-entropy-client-secret"
    encoded = security.hash_client_secret(secret)
    assert encoded != secret
    assert security.verify_client_secret(secret, encoded)
    assert not security.verify_client_secret("wrong-secret", encoded)
    assert not security.verify_client_secret(secret, "invalid")


def test_m2m_token_rejects_tampering(monkeypatch: pytest.MonkeyPatch) -> None:
    """The signed token cannot be altered without invalidating its signature."""
    settings = Settings(m2m_token_signing_secret=SecretStr("test-only-token-signing-secret-32-bytes"))
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    merchant = Merchant(name="Token test", slug=f"token-{uuid4().hex}")
    client = M2MClient(
        merchant_id=uuid4(),
        client_id="client-token-test",
        secret_hash=security.hash_client_secret("test-secret"),
        scopes=["payments:read"],
    )
    token = security.issue_access_token(client, merchant)
    assert security.decode_access_token(token)["sub"] == client.client_id
    header, payload, signature = token.split(".")
    altered = f"{header}.{payload}.{signature[:-2]}xx"
    with pytest.raises(HTTPException):
        security.decode_access_token(altered)


def test_credential_encryption_supports_key_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ciphertext is encrypted and remains decryptable with a retained previous key."""
    old_key = Fernet.generate_key()
    active_key = Fernet.generate_key()
    settings = Settings(
        mpesa_credential_encryption_keys=SecretStr(
            f"old={old_key.decode()},active={active_key.decode()}"
        ),
        mpesa_credential_active_key_id="active",
    )
    monkeypatch.setattr(core_credentials, "get_settings", lambda: settings)
    plaintext = b'{"consumer_key":"never-return-this"}'
    encrypted = encrypt_credentials(plaintext)
    assert plaintext not in encrypted
    assert decrypt_credentials(encrypted) == plaintext
    previous_ciphertext = b"old:" + Fernet(old_key).encrypt(plaintext)
    assert decrypt_credentials(previous_ciphertext) == plaintext


class FakeCore:
    """Deterministic Core substitute; no Daraja network request is made."""

    def __init__(self) -> None:
        self.stk_calls = 0
        self.registration_calls = 0
        self.validation_error: Exception | None = None
        self.next_stk_error: Exception | None = None

    async def validate_credentials(self, _context: object) -> None:
        if self.validation_error is not None:
            error = self.validation_error
            self.validation_error = None
            raise error

    async def stk_push(self, _context: object, _request: object) -> ProviderOperationResult:
        self.stk_calls += 1
        if self.next_stk_error is not None:
            error = self.next_stk_error
            self.next_stk_error = None
            raise error
        return ProviderOperationResult(
            operation="stk_push",
            outcome=OperationOutcome.ACCEPTED,
            response={
                "ResponseCode": "0",
                "CheckoutRequestID": f"ws_CO_{uuid4().hex}",
                "MerchantRequestID": f"mr_{uuid4().hex}",
                "ResponseDescription": "Success. Request accepted for processing",
            },
            provider_request_id="provider-request-test",
            http_status=200,
            retry_disposition=RetryDisposition.NEVER,
        )

    async def register_c2b_urls(self, _context: object, _request: object) -> ProviderOperationResult:
        self.registration_calls += 1
        return ProviderOperationResult(
            operation="c2b_registration",
            outcome=OperationOutcome.ACCEPTED,
            response={"ResponseCode": "0"},
            http_status=200,
            retry_disposition=RetryDisposition.NEVER,
        )

    async def aclose(self) -> None:
        return None


@pytest.mark.integration
def test_m2m_stk_callback_idempotency_tenant_scope_and_opt_in_c2b(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise API auth, PostgreSQL persistence, callbacks, and the transactional outbox."""
    key = Fernet.generate_key().decode()
    settings = Settings(
        environment="test",
        m2m_token_signing_secret=SecretStr("test-only-token-signing-secret-32-bytes"),
        mpesa_credential_encryption_keys=SecretStr(f"test={key}"),
        mpesa_credential_active_key_id="test",
        mpesa_public_base_url="https://callbacks.test.invalid",
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    monkeypatch.setattr(router_module, "get_settings", lambda: settings)
    monkeypatch.setattr(core_credentials, "get_settings", lambda: settings)
    fake_core = FakeCore()
    merchant_ids: list[UUID] = []
    payment_ids: list[UUID] = []
    integration_ids: list[UUID] = []
    client_ids: list[UUID] = []
    sync_engine = create_engine(settings.alembic_database_url(), pool_pre_ping=True)
    with TestClient(main_module.app) as client:
        main_module.app.state.mpesa_core = fake_core
        try:
            with SyncSession(sync_engine, expire_on_commit=False) as session:
                first = Merchant(name="Flow merchant", slug=f"flow-{uuid4().hex}")
                second = Merchant(name="Other merchant", slug=f"other-{uuid4().hex}")
                session.add_all([first, second])
                session.flush()
                first_client = M2MClient(
                    merchant_id=first.id,
                    client_id=f"client-{uuid4().hex}",
                    secret_hash=security.hash_client_secret("first-secret"),
                    scopes=["integrations:write", "payments:write", "payments:read"],
                )
                second_client = M2MClient(
                    merchant_id=second.id,
                    client_id=f"client-{uuid4().hex}",
                    secret_hash=security.hash_client_secret("second-secret"),
                    scopes=["integrations:write", "payments:write", "payments:read"],
                )
                session.add_all([first_client, second_client])
                session.commit()
                merchant_ids.extend([first.id, second.id])
                client_ids.extend([first_client.id, second_client.id])

            first_token = client.post("/api/v1/oauth/token", json={
                "client_id": first_client.client_id, "client_secret": "first-secret",
            })
            second_token = client.post("/api/v1/oauth/token", json={
                "client_id": second_client.client_id, "client_secret": "second-secret",
            })
            assert first_token.status_code == 200
            assert second_token.status_code == 200
            bearer = {"Authorization": f"Bearer {first_token.json()['access_token']}"}
            other_bearer = {"Authorization": f"Bearer {second_token.json()['access_token']}"}
            restricted_token = client.post("/api/v1/oauth/token", json={
                "grant_type": "client_credentials",
                "client_id": first_client.client_id,
                "client_secret": "first-secret",
                "scope": "payments:read",
            })
            restricted_bearer = {"Authorization": f"Bearer {restricted_token.json()['access_token']}"}
            create_payload = {
                "environment": "sandbox",
                "shortcode": "174379",
                "product_type": "paybill",
                "consumer_key": "test-consumer-key",
                "consumer_secret": "test-consumer-secret",
                "passkey": "test-passkey",
            }
            assert client.post("/api/v1/integrations", headers=restricted_bearer, json=create_payload).status_code == 403
            fake_core.validation_error = OAuthError("Daraja authorization was rejected")
            invalid_integration = client.post("/api/v1/integrations", headers=bearer, json=create_payload)
            assert invalid_integration.status_code == 422
            assert "test-consumer-secret" not in invalid_integration.text

            integration_response = client.post("/api/v1/integrations", headers=bearer, json=create_payload)
            assert integration_response.status_code == 201, integration_response.text
            integration = integration_response.json()
            integration_ids.append(UUID(integration["id"]))
            assert integration["status"] == "active"
            assert "test-consumer-secret" not in integration_response.text
            assert integration["stk_callback_url"].endswith(f"/{integration['integration_id']}")

            request_payload = {
                "integration_id": integration["integration_id"],
                "phone_number": "0712345678",
                "amount_minor": 10000,
                "merchant_reference": f"order-{uuid4().hex[:12]}",
                "description": "Test payment",
            }
            initiated = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-1"},
                json=request_payload,
            )
            assert initiated.status_code == 202, initiated.text
            payment = initiated.json()
            payment_ids.append(UUID(payment["id"]))
            assert payment["status"] == "pending"
            assert payment["provider_checkout_request_id"]
            replay = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-1"},
                json=request_payload,
            )
            assert replay.status_code == 202
            assert replay.json()["id"] == payment["id"]
            assert fake_core.stk_calls == 1
            conflict = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-1"},
                json={**request_payload, "amount_minor": 20000},
            )
            assert conflict.status_code == 409

            callback = {
                "Body": {"stkCallback": {
                    "MerchantRequestID": payment["provider_merchant_request_id"],
                    "CheckoutRequestID": payment["provider_checkout_request_id"],
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {"Item": [
                        {"Name": "Amount", "Value": 100},
                        {"Name": "MpesaReceiptNumber", "Value": "QAB123XYZ"},
                        {"Name": "PhoneNumber", "Value": 254712345678},
                    ]},
                }},
            }
            callback_url = f"/callbacks/mpesa/stk/{integration['integration_id']}"
            assert client.post(callback_url, json=callback).status_code == 200
            status_response = client.get(f"/api/v1/payments/{payment['id']}", headers=bearer)
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "succeeded"
            assert client.post(callback_url, json=callback).status_code == 200
            assert client.get(f"/api/v1/payments/{payment['id']}", headers=other_bearer).status_code == 404

            # A mismatched callback must be retained as evidence without marking payment paid.
            invalid_callback_payload = {
                "integration_id": integration["integration_id"],
                "phone_number": "0712345678",
                "amount_minor": 10000,
                "merchant_reference": f"invalid-{uuid4().hex[:12]}",
                "description": "Mismatch test",
            }
            invalid_initiated = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-invalid-callback"},
                json=invalid_callback_payload,
            )
            assert invalid_initiated.status_code == 202
            invalid_payment = invalid_initiated.json()
            payment_ids.append(UUID(invalid_payment["id"]))
            bad_callback = {
                "Body": {"stkCallback": {
                    "MerchantRequestID": invalid_payment["provider_merchant_request_id"],
                    "CheckoutRequestID": invalid_payment["provider_checkout_request_id"],
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {"Item": [
                        {"Name": "Amount", "Value": 99},
                        {"Name": "MpesaReceiptNumber", "Value": "BADAMOUNT1"},
                        {"Name": "PhoneNumber", "Value": 254712345678},
                    ]},
                }},
            }
            assert client.post(callback_url, json=bad_callback).status_code == 200
            still_pending = client.get(f"/api/v1/payments/{invalid_payment['id']}", headers=bearer)
            assert still_pending.json()["status"] == "pending"

            # A potentially transmitted request with no definitive response remains unknown.
            fake_core.next_stk_error = AmbiguousOutcome("test timeout after send")
            ambiguous_request = {
                **request_payload,
                "merchant_reference": f"unknown-{uuid4().hex[:12]}",
            }
            before_unknown = fake_core.stk_calls
            unknown_response = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-ambiguous"},
                json=ambiguous_request,
            )
            assert unknown_response.status_code == 202
            assert unknown_response.json()["status"] == "unknown"
            payment_ids.append(UUID(unknown_response.json()["id"]))
            unknown_replay = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-ambiguous"},
                json=ambiguous_request,
            )
            assert unknown_replay.json()["status"] == "unknown"
            assert fake_core.stk_calls == before_unknown + 1

            # A definitive provider rejection is persisted and never retried on replay.
            fake_core.next_stk_error = ProviderRejected("provider rejected test request")
            rejected_request = {
                **request_payload,
                "merchant_reference": f"rejected-{uuid4().hex[:12]}",
            }
            rejected = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-rejected"},
                json=rejected_request,
            )
            assert rejected.status_code == 422
            rejected_replay = client.post(
                "/api/v1/payments/stk",
                headers={**bearer, "Idempotency-Key": "flow-key-rejected"},
                json=rejected_request,
            )
            assert rejected_replay.status_code == 202
            assert rejected_replay.json()["status"] == "failed"

            c2b_payload = {
                "TransID": f"C2B{uuid4().hex[:10]}",
                "TransTime": "20261029120000",
                "TransAmount": "100.00",
                "BusinessShortCode": "174379",
                "BillRefNumber": "ORDER-1",
                "MSISDN": "254712345678",
            }
            disabled = client.post(
                f"/callbacks/mpesa/c2b/{integration['integration_id']}/confirmation",
                json=c2b_payload,
            )
            assert disabled.json()["ResultCode"] == 1
            registration = client.post(
                f"/api/v1/integrations/{integration['integration_id']}/c2b/register",
                headers=bearer,
            )
            assert registration.status_code == 200, registration.text
            assert fake_core.registration_calls == 1
            c2b = client.post(
                f"/callbacks/mpesa/c2b/{integration['integration_id']}/confirmation",
                json=c2b_payload,
            )
            assert c2b.status_code == 200
            assert c2b.json()["ResultCode"] == 0
            duplicate_c2b = client.post(
                f"/callbacks/mpesa/c2b/{integration['integration_id']}/confirmation",
                json=c2b_payload,
            )
            assert duplicate_c2b.json()["ResultCode"] == 0
            mismatched_duplicate = client.post(
                f"/callbacks/mpesa/c2b/{integration['integration_id']}/confirmation",
                json={**c2b_payload, "TransAmount": "200.00"},
            )
            assert mismatched_duplicate.json()["ResultCode"] == 1

            with SyncSession(sync_engine, expire_on_commit=False) as session:
                events = session.exec(select(EventOutbox).where(EventOutbox.merchant_id == merchant_ids[0])).all()
                assert len(events) == 3
                stk_callbacks = session.exec(select(ProviderCallback).where(
                    ProviderCallback.integration_id == integration_ids[0],
                    ProviderCallback.callback_type == "stk",
                )).all()
                assert len(stk_callbacks) == 2
                assert sum(row.processing_status == "processed" for row in stk_callbacks) == 1
                assert sum(row.processing_status == "rejected" for row in stk_callbacks) == 1
                session.exec(delete(EventOutbox).where(EventOutbox.merchant_id.in_(merchant_ids)))
                session.exec(delete(ProviderCallback).where(ProviderCallback.integration_id.in_(integration_ids)))
                session.exec(delete(ProviderRequest).where(ProviderRequest.merchant_id.in_(merchant_ids)))
                session.exec(delete(PaymentAttempt).where(PaymentAttempt.payment_id.in_(select(Payment.id).where(Payment.merchant_id.in_(merchant_ids)))))
                session.exec(delete(IdempotencyRecord).where(IdempotencyRecord.merchant_id.in_(merchant_ids)))
                session.exec(delete(Payment).where(Payment.merchant_id.in_(merchant_ids)))
                session.exec(delete(AuditLog).where(AuditLog.merchant_id.in_(merchant_ids)))
                session.exec(delete(DarajaIntegration).where(DarajaIntegration.id.in_(integration_ids)))
                session.exec(delete(M2MClient).where(M2MClient.id.in_(client_ids)))
                session.exec(delete(Merchant).where(Merchant.id.in_(merchant_ids)))
                session.commit()
        finally:
            main_module.app.state.mpesa_core = None
            sync_engine.dispose()
