"""Behavioral, security, and failure-path tests for the M-Pesa Core boundary."""
import asyncio
import base64
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from pydantic import SecretStr

from app.core.config import Settings
from app.models.integrations import DarajaIntegration
from app.mpesa_core.audit import redact_metadata
from app.mpesa_core.callbacks import callback_fingerprint, normalize_stk_callback
from app.mpesa_core.client import MpesaCore
from app.mpesa_core.credentials import (
    CredentialVault,
    IntegrationCredentials,
    generate_security_credential,
)
from app.mpesa_core.errors import AuditPersistenceError, CapabilityDisabled, ConfigurationError
from app.mpesa_core.schemas import OperationOutcome, STKPushRequest


class MemoryAuditor:
    """Small deterministic auditor fake; tests still assert audit-before-send ordering."""

    def __init__(self, fail_operation: str | None = None) -> None:
        self.started: list[dict[str, object]] = []
        self.finished: list[dict[str, object]] = []
        self.fail_operation = fail_operation

    async def start(self, integration, operation, request_metadata, **kwargs):
        if operation == self.fail_operation:
            raise AuditPersistenceError("audit unavailable")
        row = SimpleNamespace(id=uuid4(), correlation_id=uuid4(), operation=operation)
        self.started.append({
            "row": row,
            "operation": operation,
            "metadata": redact_metadata(request_metadata),
        })
        return row

    async def finish(self, audit_id, **kwargs):
        self.finished.append({"audit_id": audit_id, **kwargs})


def make_settings(**overrides) -> Settings:
    key = Fernet.generate_key().decode("ascii")
    values = {
        "environment": "test",
        "mpesa_credential_encryption_keys": f"v1={key}",
        "mpesa_credential_active_key_id": "v1",
        "mpesa_public_base_url": "https://pay.example.test",
        "mpesa_http_timeout_seconds": 2.0,
    }
    values.update(overrides)
    return Settings(**values)


def make_integration(settings: Settings, capabilities: list[str] | None = None) -> DarajaIntegration:
    integration = DarajaIntegration(
        merchant_id=uuid4(),
        environment="sandbox",
        status="active",
        credential_status="pending",
        shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        enabled_capabilities=capabilities or ["stk_push"],
    )
    integration.stk_callback_url = f"https://pay.example.test/callbacks/mpesa/stk/{integration.integration_id}"
    integration.c2b_validation_url = f"https://pay.example.test/callbacks/mpesa/c2b/validation/{integration.integration_id}"
    integration.c2b_confirmation_url = f"https://pay.example.test/callbacks/mpesa/c2b/confirmation/{integration.integration_id}"
    CredentialVault(settings).store(
        integration,
        consumer_key="test-consumer-key",
        consumer_secret="test-consumer-secret",
        passkey="test-passkey",
        initiator_name="test-initiator",
        initiator_password="test-initiator-password",
    )
    integration.credential_status = "valid"
    integration.status = "active"
    return integration


def client_for(settings: Settings, integration: DarajaIntegration, handler, auditor=None):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return MpesaCore(settings, http_client=http, auditor=auditor or MemoryAuditor())


def stk_callback(result_code=0, amount=15, phone=254712345678):
    return {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "merchant-request-1",
                "CheckoutRequestID": "checkout-request-1",
                "ResultCode": result_code,
                "ResultDesc": "Request processed",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": amount},
                        {"Name": "MpesaReceiptNumber", "Value": "QAB123XYZ"},
                        {"Name": "TransactionDate", "Value": "20261023120000"},
                        {"Name": "PhoneNumber", "Value": phone},
                    ]
                } if result_code == 0 else None,
            }
        }
    }


def test_credential_ciphertext_supports_key_rotation_without_plaintext_export():
    old_key = Fernet.generate_key().decode("ascii")
    new_key = Fernet.generate_key().decode("ascii")
    old_settings = make_settings(mpesa_credential_encryption_keys=f"old={old_key}", mpesa_credential_active_key_id="old")
    old_vault = CredentialVault(old_settings)
    ciphertext = old_vault.encrypt("private-consumer-secret")
    new_settings = make_settings(
        mpesa_credential_encryption_keys=f"old={old_key},new={new_key}",
        mpesa_credential_active_key_id="new",
    )
    new_vault = CredentialVault(new_settings)

    assert new_vault.decrypt(ciphertext) == "private-consumer-secret"
    rotated = new_vault.encrypt(new_vault.decrypt(ciphertext))
    assert rotated.startswith(b"new:")
    assert new_vault.decrypt(rotated) == "private-consumer-secret"
    assert b"private-consumer-secret" not in ciphertext

    integration = DarajaIntegration(merchant_id=uuid4(), environment="sandbox")
    old_vault.store(
        integration,
        consumer_key="key",
        consumer_secret="secret",
        passkey="passkey",
        initiator_name="initiator",
        initiator_password="password",
    )
    new_vault.rotate(integration)
    resolved = new_vault.resolve(integration)
    assert resolved.consumer_key == "key"
    assert resolved.consumer_secret == "secret"
    assert integration.consumer_key_ciphertext.startswith(b"new:")
    assert integration.credential_version == 3


def test_missing_encryption_key_fails_closed():
    settings = Settings()
    with pytest.raises(ConfigurationError):
        CredentialVault(settings)


def test_audit_redaction_masks_credentials_and_phone_numbers():
    redacted = redact_metadata({
        "ConsumerSecret": "not-for-logs",
        "SecurityCredential": "private",
        "PhoneNumber": "254712345678",
        "PartyA": "254712345678",
        "Amount": 1500,
    })
    assert redacted["ConsumerSecret"] == "[REDACTED]"
    assert redacted["SecurityCredential"] == "[REDACTED]"
    assert redacted["PhoneNumber"] == "***5678"
    assert redacted["PartyA"] == "***5678"
    assert redacted["Amount"] == 1500


def test_stk_callback_normalization_minimizes_pii_and_is_deterministic():
    payload = stk_callback()
    normalized = normalize_stk_callback(payload)

    assert normalized["checkout_request_id"] == "checkout-request-1"
    assert normalized["result_code"] == 0
    assert normalized["receipt_number"] == "QAB123XYZ"
    assert normalized["safe_payload"]["phone_masked"] == "***5678"
    assert "PhoneNumber" not in normalized["safe_payload"]
    assert callback_fingerprint(payload) == callback_fingerprint(payload)


def test_stk_callback_rejects_malformed_payload():
    with pytest.raises(ValueError):
        normalize_stk_callback({"Body": {}})


def test_security_credential_uses_rsa_pkcs1v15_with_environment_certificate():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Safaricom test certificate")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before((now - timedelta(days=1)).replace(tzinfo=None))
        .not_valid_after((now + timedelta(days=30)).replace(tzinfo=None))
        .sign(private_key, hashes.SHA256())
    )
    settings = make_settings(
        mpesa_sandbox_certificate_pem=SecretStr(certificate.public_bytes(serialization.Encoding.PEM).decode())
    )
    integration = DarajaIntegration(merchant_id=uuid4(), environment="sandbox")
    credentials = IntegrationCredentials("key", "secret", "passkey", "initiator", "initiator-password")
    encrypted = generate_security_credential(integration, credentials, settings)
    plaintext = private_key.decrypt(base64.b64decode(encrypted), padding.PKCS1v15())

    assert plaintext == b"initiator-password"


@pytest.mark.asyncio
async def test_stk_push_builds_typed_payload_and_only_reports_provider_acceptance():
    settings = make_settings()
    integration = make_integration(settings)
    seen: list[httpx.Request] = []
    token_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls
        seen.append(request)
        if request.url.path == "/oauth/v1/generate":
            token_calls += 1
            assert request.headers.get("Authorization", "").startswith("Basic ")
            return httpx.Response(200, json={"access_token": "short-lived-token", "expires_in": 3600})
        assert request.url.path == "/mpesa/stkpush/v1/processrequest"
        assert request.headers["Authorization"] == "Bearer short-lived-token"
        return httpx.Response(200, json={
            "ResponseCode": "0",
            "ResponseDescription": "Accepted for processing",
            "MerchantRequestID": "merchant-request-1",
            "CheckoutRequestID": "checkout-request-1",
        })

    auditor = MemoryAuditor()
    core = client_for(settings, integration, handler, auditor)
    result = await core.stk_push(
        integration,
        STKPushRequest(
            phone_number="0712345678",
            amount_minor=1500,
            account_reference="INV123",
            description="NetPay sale",
        ),
        idempotency_key="stk-success-test",
    )
    try:
        assert result.outcome is OperationOutcome.ACCEPTED
        assert result.provider_request_id == "checkout-request-1"
        assert token_calls == 1
        import json
        payload = json.loads(seen[-1].content)
        assert payload["Amount"] == 15
        assert payload["PartyA"] == "254712345678"
        assert payload["PhoneNumber"] == "254712345678"
        assert payload["CallBackURL"] == f"https://pay.example.test/callbacks/mpesa/stk/{integration.integration_id}"
        assert "test-passkey" not in repr(auditor.started)
        assert auditor.finished[-1]["outcome"] == "accepted"
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_timeout_after_send_is_unknown_and_never_retried():
    settings = make_settings()
    integration = make_integration(settings)
    stk_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal stk_calls
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        stk_calls += 1
        raise httpx.ReadTimeout("provider response timed out", request=request)

    auditor = MemoryAuditor()
    core = client_for(settings, integration, handler, auditor)
    try:
        result = await core.stk_push(
            integration,
            STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale"),
            idempotency_key="stk-timeout-test",
        )
        assert result.outcome is OperationOutcome.UNKNOWN
        assert stk_calls == 1
        assert auditor.finished[-1]["outcome"] == "unknown"
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_connect_error_is_not_sent_but_server_error_is_unknown():
    settings = make_settings()
    integration = make_integration(settings)
    mode = {"value": "connect"}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if mode["value"] == "connect":
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(503, json={"errorMessage": "temporary failure"})

    core = client_for(settings, integration, handler)
    try:
        result = await core.stk_push(
            integration,
            STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale"),
            idempotency_key="stk-connect-test",
        )
        assert result.outcome is OperationOutcome.NOT_SENT
        mode["value"] = "server"
        result = await core.stk_push(
            integration,
            STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale"),
            idempotency_key="stk-server-error-test",
        )
        assert result.outcome is OperationOutcome.UNKNOWN
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_http_rejection_and_malformed_json_are_not_marked_paid():
    settings = make_settings()
    integration = make_integration(settings)
    mode = {"value": "rejected"}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if mode["value"] == "rejected":
            return httpx.Response(400, json={"ResponseCode": "1", "ResponseDescription": "Rejected"})
        return httpx.Response(200, content=b"not-json")

    core = client_for(settings, integration, handler)
    try:
        request = STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale")
        assert (await core.stk_push(integration, request, idempotency_key="stk-rejected-test")).outcome is OperationOutcome.REJECTED
        mode["value"] = "malformed"
        assert (await core.stk_push(integration, request, idempotency_key="stk-malformed-test")).outcome is OperationOutcome.UNKNOWN
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_audit_start_failure_prevents_stk_request_from_being_sent():
    settings = make_settings()
    integration = make_integration(settings)
    stk_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal stk_calls
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        stk_calls += 1
        return httpx.Response(200, json={"ResponseCode": "0"})

    core = client_for(settings, integration, handler, MemoryAuditor(fail_operation="stk_push"))
    try:
        with pytest.raises(AuditPersistenceError):
            await core.stk_push(
                integration,
                STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale"),
                idempotency_key="stk-audit-failure-test",
            )
        assert stk_calls == 0
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_concurrent_stk_requests_share_one_oauth_exchange():
    settings = make_settings()
    integration = make_integration(settings)
    token_calls = 0
    stk_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls, stk_calls
        if request.url.path == "/oauth/v1/generate":
            token_calls += 1
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        stk_calls += 1
        return httpx.Response(200, json={"ResponseCode": "0", "CheckoutRequestID": f"checkout-{stk_calls}"})

    core = client_for(settings, integration, handler)
    request = STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale")
    try:
        results = await asyncio.gather(*(core.stk_push(integration, request, idempotency_key=f"concurrent-{index}") for index in range(8)))
        assert token_calls == 1
        assert stk_calls == 8
        assert all(result.outcome is OperationOutcome.ACCEPTED for result in results)
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_disabled_capability_fails_before_any_provider_request():
    settings = make_settings()
    integration = make_integration(settings, capabilities=["stk_push"])
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})

    core = client_for(settings, integration, handler)
    try:
        from app.mpesa_core.schemas import STKQueryRequest
        with pytest.raises(CapabilityDisabled):
            await core.stk_query(integration, STKQueryRequest(checkout_request_id="checkout"))
        assert requests == []
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_c2b_registration_is_opt_in():
    settings = make_settings()
    integration = make_integration(settings, capabilities=["stk_push"])
    core = client_for(settings, integration, lambda request: httpx.Response(200, json={}))
    try:
        from app.mpesa_core.schemas import C2BRegistrationRequest
        with pytest.raises(CapabilityDisabled):
            await core.register_c2b_urls(integration, C2BRegistrationRequest(), idempotency_key="c2b-disabled-test")
    finally:
        await core.aclose()


def test_stk_amount_must_be_whole_kes_shillings():
    with pytest.raises(ValueError):
        STKPushRequest(phone_number="254712345678", amount_minor=150, account_reference="INV", description="Sale")


@pytest.mark.asyncio
async def test_all_gated_operation_adapters_use_typed_payloads_and_expected_paths():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Daraja adapter test")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before((now - timedelta(days=1)).replace(tzinfo=None))
        .not_valid_after((now + timedelta(days=30)).replace(tzinfo=None))
        .sign(private_key, hashes.SHA256())
    )
    settings = make_settings(
        mpesa_sandbox_certificate_pem=SecretStr(certificate.public_bytes(serialization.Encoding.PEM).decode())
    )
    capabilities = [
        "stk_query", "c2b_registration", "dynamic_qr", "transaction_status",
        "account_balance", "reversal", "b2c", "b2b", "pull_transactions",
    ]
    integration = make_integration(settings, capabilities=capabilities)
    integration.c2b_enabled = True
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        paths.append(request.url.path)
        if request.url.path == "/mpesa/qrcode/v1/generate":
            return httpx.Response(200, json={"ResponseCode": "request-id", "QRCode": "base64-image-data"})
        return httpx.Response(200, json={"ResponseCode": "0", "RequestID": "request-123"})

    core = client_for(settings, integration, handler)
    from app.mpesa_core.schemas import (
        AccountBalanceRequest,
        B2BPaymentRequest,
        B2CPaymentRequest,
        C2BRegistrationRequest,
        DynamicQRRequest,
        PullTransactionsRequest,
        ReversalRequest,
        STKQueryRequest,
        TransactionStatusRequest,
    )

    now = datetime.now(UTC)
    calls = [
        core.stk_query(integration, STKQueryRequest(checkout_request_id="checkout-123")),
        core.register_c2b_urls(integration, C2BRegistrationRequest(), idempotency_key="c2b-enabled-test"),
        core.dynamic_qr(integration, DynamicQRRequest(
            merchant_name="Test merchant", reference="INV-1", amount_minor=100,
            transaction_code="PB", credit_party_identifier="174379",
        )),
        core.transaction_status(integration, TransactionStatusRequest(transaction_id="QAB123XYZ")),
        core.account_balance(integration, AccountBalanceRequest()),
        core.reverse_transaction(integration, ReversalRequest(
            transaction_id="QAB123XYZ", amount_minor=100, receiver_party="174379", remarks="approved test",
        ), idempotency_key="reversal-test"),
        core.b2c_payment(integration, B2CPaymentRequest(
            phone_number="0712345678", amount_minor=100, remarks="approved test",
        ), idempotency_key="b2c-test"),
        core.b2b_payment(integration, B2BPaymentRequest(
            party_b="600000", amount_minor=100, command_id="BusinessPayBill", remarks="approved test",
        ), idempotency_key="b2b-test"),
        core.pull_transactions(integration, PullTransactionsRequest(
            start_date=now - timedelta(days=1), end_date=now, account_number="test-account",
        )),
    ]
    try:
        results = await asyncio.gather(*calls)
        assert all(result.outcome is OperationOutcome.ACCEPTED for result in results)
        assert set(paths) == {
            "/mpesa/stkpushquery/v1/query",
            "/mpesa/c2b/v1/registerurl",
            "/mpesa/qrcode/v1/generate",
            "/mpesa/transactionstatus/v1/query",
            "/mpesa/accountbalance/v1/query",
            "/mpesa/reversal/v1/request",
            "/mpesa/b2c/v3/paymentrequest",
            "/mpesa/b2b/v1/paymentrequest",
            "/mpesa/pulltransactions/v1/query",
        }
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_provider_operation_audit_is_durable_and_redacted():
    from app.core.database import create_database_engine, create_session_factory
    from app.models.merchants import Merchant
    from app.models.operations import ProviderRequest
    from app.mpesa_core.audit import ProviderOperationAuditor

    settings = Settings(environment="test")
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    merchant = Merchant(name="Audit test merchant", slug=f"mpesa-audit-{uuid4().hex}")
    integration = None
    audit_row = None
    try:
        async with factory() as session:
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)
            integration = DarajaIntegration(
                merchant_id=merchant.id,
                environment="sandbox",
                status="active",
                credential_status="valid",
                shortcode="174379",
            )
            session.add(integration)
            await session.commit()
            await session.refresh(integration)

        auditor = ProviderOperationAuditor(factory)
        audit_row = await auditor.start(
            integration,
            "stk_push",
            {"PhoneNumber": "254712345678", "Password": "must-not-persist", "Amount": 15},
        )
        await auditor.finish(
            audit_row.id,
            outcome="accepted",
            http_status=200,
            provider_request_id="checkout-123",
            response_metadata={"ResponseCode": "0", "ConsumerSecret": "must-not-persist"},
        )
        async with factory() as session:
            stored = await session.get(ProviderRequest, audit_row.id)
            assert stored is not None
            assert stored.outcome == "accepted"
            assert stored.request_metadata["PhoneNumber"] == "***5678"
            assert stored.request_metadata["Password"] == "[REDACTED]"
            assert stored.response_metadata["ConsumerSecret"] == "[REDACTED]"
            await session.delete(stored)
            await session.commit()
    finally:
        async with factory() as session:
            if audit_row is not None:
                stored_audit = await session.get(ProviderRequest, audit_row.id)
                if stored_audit is not None:
                    await session.delete(stored_audit)
            if integration is not None:
                stored_integration = await session.get(DarajaIntegration, integration.id)
                if stored_integration is not None:
                    await session.delete(stored_integration)
            stored_merchant = await session.get(Merchant, merchant.id)
            if stored_merchant is not None:
                await session.delete(stored_merchant)
            await session.commit()
        await engine.dispose()
