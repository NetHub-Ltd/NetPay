"""Payment initiation idempotency and ambiguity regression tests."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from cryptography.fernet import Fernet

from app.api.payments import PaymentCreateRequest, _request_hash, create_payment
from app.core.config import Settings
from app.core.machine_auth import MachinePrincipal
from app.models.attempts import PaymentAttempt
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient
from app.models.operations import ProviderRequest
from app.models.payments import IdempotencyRecord, Payment
from app.providers.daraja import DarajaStkUncertain


def _result(value: object) -> MagicMock:
    result = MagicMock()
    result.first.return_value = value
    return result


def _settings(key: str) -> Settings:
    return Settings(
        environment="test",
        secret_key="test-signing-key-that-is-at-least-32-bytes-long",
        credential_encryption_key=key,
        daraja_timeout_seconds=3,
    )


def _body(amount: int = 100) -> PaymentCreateRequest:
    return PaymentCreateRequest(
        integration_id="int_test-integration",
        merchant_reference="order-123",
        amount_kes=amount,
        phone_number="0712345678",
        description="Order payment",
    )


def _principal(merchant_id) -> MachinePrincipal:
    return MachinePrincipal(
        client_id="nmc_test-client",
        merchant_id=merchant_id,
        scopes=frozenset({"payments:write", "payments:read"}),
    )


def _session_for_new_payment(merchant_id, key: str) -> tuple[MagicMock, DarajaIntegration, M2MClient]:
    integration = DarajaIntegration(
        merchant_id=merchant_id,
        integration_id="int_test-integration",
        environment="sandbox",
        status="active",
        credential_status="valid",
        shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        consumer_key_ciphertext=b"key",
        consumer_secret_ciphertext=b"secret",
        passkey_ciphertext=b"passkey",
        stk_callback_url="https://pay.example.test/v1/callbacks/stk/int_test-integration",
    )
    client = M2MClient(
        merchant_id=merchant_id,
        client_id="nmc_test-client",
        secret_hash="hash",
        scopes=["payments:read", "payments:write"],
        status="active",
    )
    session = MagicMock()
    session.exec = AsyncMock(
        side_effect=[
            _result(None),
            _result(integration),
            _result(None),
            _result(client),
        ]
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session, integration, client


@pytest.mark.asyncio
async def test_payment_persists_idempotency_and_provider_records_before_stk_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An accepted STK request remains pending and uses the merchant integration."""
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr("app.api.payments.get_settings", lambda: _settings(key))
    monkeypatch.setattr(
        "app.api.payments.decrypt_credential",
        lambda ciphertext, key: {
            b"key": "consumer-key",
            b"secret": "consumer-secret",
            b"passkey": "passkey",
        }[ciphertext],
    )
    provider_calls: list[dict[str, object]] = []

    async def initiate(**kwargs: object) -> dict[str, str]:
        provider_calls.append(kwargs)
        return {
            "checkout_request_id": "ws_CO_checkout",
            "merchant_request_id": "merchant-request",
            "response_code": "0",
        }

    monkeypatch.setattr("app.api.payments.initiate_stk_push", initiate)
    merchant_id = uuid4()
    session, integration, client = _session_for_new_payment(merchant_id, key)

    response = await create_payment(_body(), "idempotency-key-123", _principal(merchant_id), session)

    records = [call.args[0] for call in session.add.call_args_list]
    payment = next(record for record in records if isinstance(record, Payment))
    attempt = next(record for record in records if isinstance(record, PaymentAttempt))
    request = next(record for record in records if isinstance(record, ProviderRequest))
    idempotency = next(record for record in records if isinstance(record, IdempotencyRecord))
    assert response.status == "pending"
    assert response.amount_minor == 10_000
    assert response.provider_checkout_request_id == "ws_CO_checkout"
    assert payment.phone_number == "254712345678"
    assert payment.integration_id == integration.id
    assert attempt.payment_id == payment.id
    assert request.payment_id == payment.id
    assert idempotency.resource_id == payment.id
    assert idempotency.client_id == client.id
    assert provider_calls[0]["consumer_secret"] == "consumer-secret"
    assert provider_calls[0]["amount_kes"] == 100
    assert provider_calls[0]["account_reference"] == "NP" + payment.id.hex[:10]
    assert "consumer_secret" not in request.request_metadata
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_idempotency_replay_returns_existing_payment_without_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exact replay returns the stored resource and never issues another STK request."""
    merchant_id = uuid4()
    body = _body()
    payment = Payment(
        merchant_id=merchant_id,
        integration_id=uuid4(),
        merchant_reference=body.merchant_reference,
        amount_minor=body.amount_kes * 100,
        status="pending",
    )
    record = IdempotencyRecord(
        merchant_id=merchant_id,
        key="idempotency-key-123",
        request_hash=_request_hash(body),
        resource_id=payment.id,
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_result(record), _result(payment)])
    provider = AsyncMock()
    monkeypatch.setattr("app.api.payments.initiate_stk_push", provider)

    response = await create_payment(body, "idempotency-key-123", _principal(merchant_id), session)
    assert response.payment_id == payment.id
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_idempotency_key_cannot_be_reused_with_different_payload() -> None:
    """Changed request data with an existing key returns conflict before provider I/O."""
    merchant_id = uuid4()
    first_body = _body()
    record = IdempotencyRecord(
        merchant_id=merchant_id,
        key="idempotency-key-123",
        request_hash=_request_hash(first_body),
        resource_id=uuid4(),
    )
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(record))

    with pytest.raises(HTTPException) as error:
        await create_payment(_body(amount=200), "idempotency-key-123", _principal(merchant_id), session)
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_ambiguous_stk_timeout_is_unknown_and_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """A network-ambiguous provider result stays unknown for reconciliation."""
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr("app.api.payments.get_settings", lambda: _settings(key))
    monkeypatch.setattr(
        "app.api.payments.decrypt_credential",
        lambda ciphertext, key: "decrypted-secret",
    )

    async def uncertain(**kwargs: object) -> dict[str, str]:
        raise DarajaStkUncertain("provider outcome unknown")

    monkeypatch.setattr("app.api.payments.initiate_stk_push", uncertain)
    merchant_id = uuid4()
    session, _, _ = _session_for_new_payment(merchant_id, key)

    response = await create_payment(_body(), "idempotency-key-123", _principal(merchant_id), session)
    assert response.status == "unknown"
    assert response.provider_checkout_request_id is None
