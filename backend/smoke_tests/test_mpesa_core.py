"""Exhaustive mocked contract and failure-path tests for mpesa_core."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.mpesa_core.callbacks import (
    callback_fingerprint,
    parse_async_result_callback,
    parse_c2b_callback,
    parse_stk_callback,
)
from app.mpesa_core.client import MpesaCore
from app.mpesa_core.errors import (
    AmbiguousOutcome,
    CapabilityDisabled,
    CatalogueContractUnavailable,
    InvalidRequest,
    OAuthError,
    OperationOutcome,
    ProviderRejected,
    TransportFailure,
)
from app.mpesa_core.schemas import (
    AccountBalanceRequest,
    B2BPaymentRequest,
    B2CPaymentRequest,
    C2BRegistrationRequest,
    C2BSimulationRequest,
    DarajaCredentials,
    DynamicQRRequest,
    IntegrationContext,
    ReversalRequest,
    STKPushRequest,
    STKQueryRequest,
    TaxRemittanceRequest,
    TransactionStatusRequest,
)
from app.mpesa_core.validation import normalize_ke_phone, validate_callback_url


def context(
    *,
    environment: str = "sandbox",
    capabilities: set[str] | None = None,
) -> IntegrationContext:
    return IntegrationContext(
        integration_id="int_test_01",
        environment=environment,
        shortcode="174379",
        party_b_shortcode="174379",
        enabled_capabilities=frozenset(capabilities or {
            "stk_push", "stk_query", "c2b_registration", "c2b_simulation", "dynamic_qr",
            "transaction_status", "account_balance", "reversal", "b2c", "b2b",
            "tax_remittance", "pull_transactions", "bill_manager", "ratiba",
            "lipa_na_bonga", "b2b_express_checkout",
        }),
        credentials=DarajaCredentials(
            consumer_key=SecretStr("consumer-key-test"),
            consumer_secret=SecretStr("consumer-secret-test"),
            passkey=SecretStr("passkey-test"),
            initiator_name="test-initiator",
            security_credential=SecretStr("encrypted-security-credential-test"),
            credential_version=1,
        ),
    )


def settings() -> Any:
    class SettingsStub:
        mpesa_http_timeout_seconds = 2.0
        mpesa_public_base_url = "https://payments.example.test/callback"
    return SettingsStub()


def handler_for(routes: dict[str, Any], seen: list[httpx.Request] | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "oauth-token-test", "expires_in": 3600})
        result = routes.get(request.url.path)
        if isinstance(result, Exception):
            raise result
        if callable(result):
            return result(request)
        if result is None:
            return httpx.Response(200, json={"ResponseCode": "0", "ResponseDescription": "Accepted",
                                             "RequestID": "request-123", "ConversationID": "conversation-123"})
        return result
    return handler


@pytest.mark.parametrize(("phone", "expected"), [
    ("0712345678", "254712345678"),
    ("712345678", "254712345678"),
    ("254712345678", "254712345678"),
    ("+254712345678", "254712345678"),
    ("01 12345678", "2541112345678"),
])
def test_normalizes_supported_kenyan_phone_formats(phone: str, expected: str) -> None:
    assert normalize_ke_phone(phone) == expected


@pytest.mark.parametrize("phone", ["", "123", "254123456789", "07123", "abc0712345678", "+2547123456789"])
def test_rejects_invalid_phone(phone: str) -> None:
    with pytest.raises(InvalidRequest):
        normalize_ke_phone(phone)


def test_callback_url_requires_absolute_http_url_and_https_in_production() -> None:
    assert validate_callback_url("https://example.test/callback", production=True)
    with pytest.raises(InvalidRequest):
        validate_callback_url("http://example.test/callback", production=True)
    with pytest.raises(InvalidRequest):
        validate_callback_url("https://user:pass@example.test/callback", production=False)
    with pytest.raises(InvalidRequest):
        validate_callback_url("/relative/path", production=False)


def test_stk_request_rejects_fractional_kes() -> None:
    with pytest.raises(ValidationError):
        STKPushRequest(phone_number="0712345678", amount_minor=150, account_reference="INV", description="Sale")


@pytest.mark.asyncio
async def test_stk_push_builds_documented_payload_and_returns_acceptance_only() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        result = await core.stk_push(context(), STKPushRequest(
            phone_number="0712345678", amount_minor=1500, account_reference="INV-123", description="NetPay sale",
        ))
        assert result.outcome is OperationOutcome.ACCEPTED
        assert result.provider_request_id == "request-123"
        request = next(r for r in seen if r.url.path == "/mpesa/stkpush/v1/processrequest")
        payload = json.loads(request.content)
        assert payload["Amount"] == 15
        assert payload["PartyA"] == "254712345678"
        assert payload["PhoneNumber"] == "254712345678"
        assert payload["CallBackURL"] == "https://payments.example.test/callback"
        assert payload["Password"] != "passkey-test"
        assert "oauth-token-test" not in repr(result)
        assert "consumer-secret-test" not in repr(result)
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_oauth_requests_are_shared_under_concurrency() -> None:
    calls = {"oauth": 0, "stk": 0}
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            calls["oauth"] += 1
            return httpx.Response(200, json={"access_token": "shared-token", "expires_in": 3600})
        calls["stk"] += 1
        return httpx.Response(200, json={"ResponseCode": "0", "CheckoutRequestID": f"checkout-{calls['stk']}"})
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    req = STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale")
    try:
        results = await asyncio.gather(*(core.stk_push(context(), req) for _ in range(8)))
        assert calls == {"oauth": 1, "stk": 8}
        assert all(r.outcome is OperationOutcome.ACCEPTED for r in results)
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_oauth_rejection_is_typed_and_does_not_leak_secrets() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client", "error_description": "secret consumer-secret-test"})
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(OAuthError) as error:
            await core.stk_query(context(), STKQueryRequest(checkout_request_id="checkout"))
        assert "consumer-secret-test" not in str(error.value)
        assert "secret" not in str(error.value)
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_provider_rejection_is_normalized() -> None:
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({
        "/mpesa/qrcode/v1/generate": httpx.Response(400, json={"ResponseCode": "1", "ResponseDescription": "no"})
    })))
    try:
        with pytest.raises(ProviderRejected):
            await core.dynamic_qr(context(), DynamicQRRequest(
                merchant_name="Test Shop", reference="INV-1", amount_minor=100,
                transaction_code="PB", credit_party_identifier="174379",
            ))
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_malformed_provider_json_is_not_treated_as_success() -> None:
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({
        "/mpesa/qrcode/v1/generate": httpx.Response(200, content=b"not-json")
    })))
    try:
        from app.mpesa_core.errors import MalformedProviderResponse
        with pytest.raises(MalformedProviderResponse):
            await core.dynamic_qr(context(), DynamicQRRequest(
                merchant_name="Test Shop", reference="INV-1", amount_minor=100,
                transaction_code="PB", credit_party_identifier="174379",
            ))
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_connect_failure_is_not_sent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        raise httpx.ConnectError("connection refused", request=request)
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TransportFailure):
            await core.dynamic_qr(context(), DynamicQRRequest(
                merchant_name="Test Shop", reference="INV-1", amount_minor=100,
                transaction_code="PB", credit_party_identifier="174379",
            ))
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_timeout_after_possible_send_is_ambiguous_and_not_retried() -> None:
    attempts = 0
    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(AmbiguousOutcome):
            await core.stk_push(context(), STKPushRequest(
                phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale",
            ))
        assert attempts == 1
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_disabled_capability_fails_before_network_call() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        with pytest.raises(CapabilityDisabled):
            await core.stk_query(context(capabilities={"stk_push"}), STKQueryRequest(checkout_request_id="x"))
        assert seen == []
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_c2b_simulation_cannot_run_in_production() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        with pytest.raises(CapabilityDisabled):
            await core.simulate_c2b(context(environment="production"), C2BSimulationRequest(
                phone_number="254712345678", amount_minor=100, bill_reference="INV",
            ))
        assert seen == []
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_c2b_registration_uses_documented_payload_and_is_capability_gated() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        result = await core.register_c2b_urls(context(), C2BRegistrationRequest(
            validation_url="https://payments.example.test/c2b/validation",
            confirmation_url="https://payments.example.test/c2b/confirmation",
        ))
        request = next(r for r in seen if r.url.path == "/mpesa/c2b/v1/registerurl")
        payload = json.loads(request.content)
        assert payload["ShortCode"] == "174379"
        assert payload["ResponseType"] == "Completed"
        assert result.outcome is OperationOutcome.ACCEPTED
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_all_verified_adapter_paths_and_asynchronous_acknowledgements() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    ctx = context()
    try:
        calls = [
            core.stk_query(ctx, STKQueryRequest(checkout_request_id="checkout")),
            core.dynamic_qr(ctx, DynamicQRRequest(merchant_name="Shop", reference="INV", amount_minor=100,
                                                   transaction_code="PB", credit_party_identifier="174379")),
            core.transaction_status(ctx, TransactionStatusRequest(transaction_id="QAB123", result_url="https://example.test/result",
                                                                    timeout_url="https://example.test/timeout")),
            core.account_balance(ctx, AccountBalanceRequest(result_url="https://example.test/result",
                                                             timeout_url="https://example.test/timeout")),
            core.reverse_transaction(ctx, ReversalRequest(transaction_id="QAB123", amount_minor=100,
                                                            receiver_party="174379", result_url="https://example.test/result",
                                                            timeout_url="https://example.test/timeout")),
            core.b2c_payment(ctx, B2CPaymentRequest(phone_number="0712345678", amount_minor=100,
                                                     originator_conversation_id="netpay-test-1",
                                                     result_url="https://example.test/result",
                                                     timeout_url="https://example.test/timeout")),
            core.b2b_payment(ctx, B2BPaymentRequest(party_b="600000", amount_minor=100,
                                                     command_id="BusinessPayBill",
                                                     result_url="https://example.test/result",
                                                     timeout_url="https://example.test/timeout")),
            core.tax_remittance(ctx, TaxRemittanceRequest(prn="PRN123", amount_minor=100,
                                                           result_url="https://example.test/result",
                                                           timeout_url="https://example.test/timeout")),
        ]
        results = await asyncio.gather(*calls)
        assert all(r.outcome is OperationOutcome.ACCEPTED for r in results)
        assert {r.url.path for r in seen} >= {
            "/mpesa/stkpushquery/v1/query", "/mpesa/qrcode/v1/generate",
            "/mpesa/transactionstatus/v1/query", "/mpesa/accountbalance/v1/query",
            "/mpesa/reversal/v1/request", "/mpesa/b2c/v3/paymentrequest",
            "/mpesa/b2b/v1/paymentrequest", "/mpesa/b2b/v1/remittax",
        }
        b2c = json.loads(next(r for r in seen if r.url.path == "/mpesa/b2c/v3/paymentrequest").content)
        assert b2c["PartyB"] == "254712345678"
        assert b2c["Amount"] == 1
        tax = json.loads(next(r for r in seen if r.url.path == "/mpesa/b2b/v1/remittax").content)
        assert tax["CommandID"] == "PayTaxToKRA"
        assert tax["PartyB"] == "572572"
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_unverified_catalogue_contract_fails_closed_without_http_request() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        with pytest.raises(CatalogueContractUnavailable):
            await core.catalogue_operation(context(), "bill_manager", {"some": "guess"})
        assert seen == []
    finally:
        await core.aclose()


def test_stk_callback_parsing_does_not_make_authenticity_claims() -> None:
    parsed = parse_stk_callback({"Body": {"stkCallback": {
        "MerchantRequestID": "merchant-1", "CheckoutRequestID": "checkout-1",
        "ResultCode": 0, "ResultDesc": "Success",
        "CallbackMetadata": {"Item": [{"Name": "MpesaReceiptNumber", "Value": "QAB123"}]},
    }}})
    assert parsed.checkout_request_id == "checkout-1"
    assert parsed.result_code == 0


def test_c2b_callback_and_async_result_payloads_validate() -> None:
    c2b = parse_c2b_callback({
        "TransID": "QAB123", "TransTime": "20261028123456", "TransAmount": "10.00",
        "BusinessShortCode": "174379", "MSISDN": "254712345678", "BillRefNumber": "INV-1",
    })
    assert c2b.trans_id == "QAB123"
    assert parse_async_result_callback({"Result": {"ResultCode": 0}}).result["ResultCode"] == 0


def test_callback_fingerprint_is_deterministic_and_payload_is_bounded() -> None:
    payload = {"TransID": "QAB123", "TransAmount": "10"}
    assert callback_fingerprint(payload) == callback_fingerprint(payload)
    with pytest.raises(InvalidRequest):
        callback_fingerprint({"payload": "x" * 130_000})


def test_stk_callback_rejects_malformed_envelope() -> None:
    with pytest.raises(InvalidRequest):
        parse_stk_callback({"Body": {}})
