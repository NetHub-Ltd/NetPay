"""Exhaustive mocked contract and failure-path tests for mpesa_core."""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
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
    InvalidRequest,
    MalformedProviderResponse,
    MissingCredential,
    OAuthError,
    OperationOutcome,
    ProviderRejected,
    TransportFailure,
)
from app.mpesa_core.schemas import (
    BillManagerBulkCancelInvoiceRequest,
    BillManagerBulkInvoiceRequest,
    LipaNaBongaQuoteRequest,
    B2BExpressCheckoutRequest,
    BillManagerCancelInvoiceRequest,
    BillManagerInvoiceItem,
    BillManagerInvoiceRequest,
    BillManagerOptInRequest,
    BillManagerReconciliationRequest,
    LipaNaBongaRequest,
    PullTransactionsRegistrationRequest,
    PullTransactionsRequest,
    RatibaStandingOrderRequest,
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
        if result is None and request.url.path == "/mpesa/qrcode/v1/generate":
            return httpx.Response(200, json={"ResponseCode": "0", "ResponseDescription": "Accepted",
                                             "QRCode": "test-qr-payload", "RequestID": "request-123"})
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
    ("01 12345678", "254112345678"),
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
        STKPushRequest(phone_number="0712345678", amount_minor=150, account_reference="INV", description="Sale", callback_url="https://example.test/stk")


@pytest.mark.asyncio
async def test_stk_push_builds_documented_payload_and_returns_acceptance_only() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        result = await core.stk_push(context(), STKPushRequest(
            phone_number="0712345678", amount_minor=1500, account_reference="INV-123", description="NetPay sale",
            callback_url="https://payments.example.test/callback/int_test_01",
        ))
        assert result.outcome is OperationOutcome.ACCEPTED
        assert result.provider_request_id == "request-123"
        request = next(r for r in seen if r.url.path == "/mpesa/stkpush/v1/processrequest")
        payload = json.loads(request.content)
        assert payload["Amount"] == 15
        assert payload["PartyA"] == "254712345678"
        assert payload["PhoneNumber"] == "254712345678"
        assert payload["CallBackURL"] == "https://payments.example.test/callback/int_test_01"
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
    req = STKPushRequest(phone_number="254712345678", amount_minor=100, account_reference="INV", description="Sale", callback_url="https://example.test/stk")
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
                callback_url="https://example.test/stk",
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
        await core.simulate_c2b(context(), C2BSimulationRequest(
            phone_number="0712345678", amount_minor=1000, bill_reference="ORDER-1",
        ))
        request = next(r for r in seen if r.url.path == "/mpesa/c2b/v1/registerurl")
        simulation = next(r for r in seen if r.url.path == "/mpesa/c2b/v1/simulate")
        simulation_payload = json.loads(simulation.content)
        assert simulation_payload["CommandID"] == "CustomerPayBillOnline"
        assert simulation_payload["Msisdn"] == "254712345678"
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
        assert b2c["InitiatorName"] == "test-initiator"
        assert "OriginatorConversationID" not in b2c
        tax = json.loads(next(r for r in seen if r.url.path == "/mpesa/b2b/v1/remittax").content)
        assert tax["CommandID"] == "PayTaxToKRA"
        assert tax["PartyB"] == "572572"
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


@pytest.mark.asyncio
async def test_pull_transactions_registration_and_query_contracts() -> None:
    from datetime import UTC, datetime, timedelta
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    now = datetime.now(UTC)
    try:
        await core.register_pull_transactions(context(), PullTransactionsRegistrationRequest(
            nominated_phone_number="0712345678", callback_url="https://example.test/pull",
        ))
        await core.pull_transactions(context(), PullTransactionsRequest(
            start_at=now - timedelta(hours=2), end_at=now,
        ))
        registration = json.loads(next(r for r in seen if r.url.path == "/pulltransactions/v1/register").content)
        query = json.loads(next(r for r in seen if r.url.path == "/pulltransactions/v1/query").content)
        assert registration["NominatedNumber"] == "254712345678"
        assert query["ShortCode"] == "174379"
        assert query["OffSetValue"] == "0"
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_b2b_express_ratiba_and_bonga_use_their_documented_paths() -> None:
    from datetime import date, timedelta
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        await core.b2b_express_checkout(context(), B2BExpressCheckoutRequest(
            primary_shortcode="600111", receiver_shortcode="174379", amount_minor=10000,
            reference="INV-1", partner_name="NetPay", callback_url="https://example.test/express",
            request_ref_id="netpay-express-1",
        ))
        await core.create_ratiba_order(context(), RatibaStandingOrderRequest(
            standing_order_name="Subscription-1", transaction_type="Standing Order Customer Pay Bill",
            amount_minor=50000, phone_number="0712345678", callback_url="https://example.test/ratiba",
            account_reference="SUB-1", description="Subscription", frequency="5",
            start_date=date.today().strftime("%Y%m%d"),
            end_date=(date.today() + timedelta(days=365)).strftime("%Y%m%d"),
        ))
        await core.redeem_lipa_na_bonga(context(), LipaNaBongaRequest(
            phone_number="0712345678", amount_minor=8000, bonga_points=400, account_reference="INV-22",
        ))
        assert {r.url.path for r in seen} >= {
            "/v1/ussdpush/get-msisdn",
            "/standingorder/v1/createStandingOrderExternal",
            "/v1/lipa/na/bonga/redeem-paybill",
        }
        express = json.loads(next(r for r in seen if r.url.path == "/v1/ussdpush/get-msisdn").content)
        assert express["requestRefID"] == "netpay-express-1"
        ratiba = json.loads(next(r for r in seen if r.url.path == "/standingorder/v1/createStandingOrderExternal").content)
        assert ratiba["Frequency"] == "5"
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_bill_manager_typed_operations_use_distinct_endpoints() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        await core.bill_manager_opt_in(context(), BillManagerOptInRequest(
            email="billing@example.test", official_contact="0712345678",
            callback_url="https://example.test/bill-manager",
        ))
        await core.bill_manager_single_invoice(context(), BillManagerInvoiceRequest(
            external_reference="INV-1", billed_full_name="Test Customer",
            billed_phone_number="0712345678", amount_minor=150000, due_date="2026-11-15",
            account_reference="ACC-1", invoice_name="November service",
            invoice_items=[BillManagerInvoiceItem(item_name="Service", amount_minor=150000)],
        ))
        await core.bill_manager_cancel_invoice(context(), BillManagerCancelInvoiceRequest(external_reference="INV-1"))
        await core.bill_manager_reconcile_payment(context(), BillManagerReconciliationRequest(
            external_reference="INV-1", transaction_id="QAB123", amount_minor=150000,
        ))
        assert {r.url.path for r in seen} >= {
            "/v1/billmanager-invoice/optin",
            "/v1/billmanager-invoice/single-invoicing",
            "/v1/billmanager-invoice/cancel-single-invoice",
            "/v1/billmanager-invoice/reconciliation",
        }
    finally:
        await core.aclose()


def test_ratiba_date_and_pull_window_validation() -> None:
    from datetime import UTC, datetime
    with pytest.raises(ValidationError):
        RatibaStandingOrderRequest(
            standing_order_name="Monthly", transaction_type="Standing Order Customer Pay Bill",
            amount_minor=100, phone_number="0712345678", callback_url="https://example.test/cb",
            account_reference="SUB", description="Monthly", frequency="5",
            start_date="2026-01-01", end_date="20270101",
        )
    with pytest.raises(ValidationError):
        PullTransactionsRequest(
            start_at=datetime(2026, 1, 2, tzinfo=UTC),
            end_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


@pytest.mark.asyncio
async def test_provider_response_metadata_redacts_secret_fields_and_masks_phone() -> None:
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({
        "/mpesa/qrcode/v1/generate": httpx.Response(200, json={
            "ResponseCode": "0", "QRCode": "base64-data",
            "ConsumerSecret": "do-not-return-this",
            "PhoneNumber": "254712345678",
        })
    })))
    try:
        result = await core.dynamic_qr(context(), DynamicQRRequest(
            merchant_name="Shop", reference="INV", amount_minor=100,
            transaction_code="PB", credit_party_identifier="174379",
        ))
        assert result.response["ConsumerSecret"] == "[REDACTED]"
        assert result.response["PhoneNumber"] == "***5678"
        assert "do-not-return-this" not in repr(result)
        assert "254712345678" not in repr(result)
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_bill_manager_bulk_update_and_bonga_quote_endpoints() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    invoice = BillManagerInvoiceRequest(
        external_reference="INV-2", billed_full_name="Test Customer",
        billed_phone_number="0712345678", amount_minor=10000, due_date="2026-11-15",
        account_reference="ACC-2", invoice_name="Service",
    )
    try:
        await core.bill_manager_bulk_invoices(context(), BillManagerBulkInvoiceRequest(invoices=[invoice]))
        await core.bill_manager_cancel_bulk_invoices(context(), BillManagerBulkCancelInvoiceRequest(
            external_references=["INV-2", "INV-3"],
        ))
        await core.bill_manager_update_opt_in(context(), BillManagerOptInRequest(
            email="billing@example.test", official_contact="0712345678",
            callback_url="https://example.test/bill-manager",
        ))
        await core.bill_manager_update_invoice(context(), invoice)
        await core.bill_manager_update_bulk_invoices(context(), BillManagerBulkInvoiceRequest(invoices=[invoice]))
        await core.calculate_lipa_na_bonga_value(context(), LipaNaBongaQuoteRequest(bonga_points=400))
        assert {r.url.path for r in seen} >= {
            "/v1/billmanager-invoice/bulk-invoicing",
            "/v1/billmanager-invoice/cancel-bulk-invoice",
            "/v1/billmanager-invoice/change-optin-details",
            "/v1/billmanager-invoice/change-invoice",
            "/v1/billmanager-invoice/change-invoices",
            "/v1/lipa/na/bonga/calculate-points",
        }
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_initiator_password_is_rsa_encrypted_with_environment_certificate() -> None:
    from datetime import UTC, datetime, timedelta
    from app.mpesa_core.schemas import DarajaCredentials
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Daraja test certificate")])
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
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
    class CertificateSettings:
        mpesa_http_timeout_seconds = 2.0
        mpesa_sandbox_certificate_pem = SecretStr(pem)
        mpesa_production_certificate_pem = None
    ctx = context()
    ctx = ctx.model_copy(update={"credentials": DarajaCredentials(
        consumer_key=SecretStr("consumer-key-test"),
        consumer_secret=SecretStr("consumer-secret-test"),
        initiator_name="test-initiator",
        initiator_password=SecretStr("initiator-password-test"),
    )})
    core = MpesaCore(CertificateSettings(), transport=httpx.MockTransport(handler_for({})))
    try:
        payload = core._initiator_payload(ctx)
        encrypted = base64.b64decode(payload["SecurityCredential"])
        plaintext = private_key.decrypt(encrypted, padding.PKCS1v15())
        assert plaintext == b"initiator-password-test"
        assert payload["Initiator"] == "test-initiator"
    finally:
        await core.aclose()


def all_operation_calls(ctx: IntegrationContext):
    """Build every supported typed operation for shared contract-failure tests."""
    from datetime import UTC, datetime, timedelta
    invoice = BillManagerInvoiceRequest(
        external_reference="INV-X", billed_full_name="Customer", billed_phone_number="0712345678",
        amount_minor=100, due_date="2026-11-15", account_reference="ACC-X", invoice_name="Service",
    )
    now = datetime.now(UTC)
    return [
        ("stk_push", lambda core: core.stk_push(ctx, STKPushRequest(
            phone_number="0712345678", amount_minor=100, account_reference="INV", description="Sale",
            callback_url="https://example.test/stk"))),
        ("stk_query", lambda core: core.stk_query(ctx, STKQueryRequest(checkout_request_id="checkout"))),
        ("c2b_registration", lambda core: core.register_c2b_urls(ctx, C2BRegistrationRequest(
            validation_url="https://example.test/validate", confirmation_url="https://example.test/confirm"))),
        ("c2b_simulation", lambda core: core.simulate_c2b(ctx, C2BSimulationRequest(
            phone_number="0712345678", amount_minor=100, bill_reference="INV"))),
        ("dynamic_qr", lambda core: core.dynamic_qr(ctx, DynamicQRRequest(
            merchant_name="Shop", reference="INV", amount_minor=100, transaction_code="PB", credit_party_identifier="174379"))),
        ("transaction_status", lambda core: core.transaction_status(ctx, TransactionStatusRequest(
            transaction_id="QAB123", result_url="https://example.test/result", timeout_url="https://example.test/timeout"))),
        ("account_balance", lambda core: core.account_balance(ctx, AccountBalanceRequest(
            result_url="https://example.test/result", timeout_url="https://example.test/timeout"))),
        ("reversal", lambda core: core.reverse_transaction(ctx, ReversalRequest(
            transaction_id="QAB123", amount_minor=100, receiver_party="174379",
            result_url="https://example.test/result", timeout_url="https://example.test/timeout"))),
        ("b2c", lambda core: core.b2c_payment(ctx, B2CPaymentRequest(
            phone_number="0712345678", amount_minor=100,
            result_url="https://example.test/result", timeout_url="https://example.test/timeout"))),
        ("b2b", lambda core: core.b2b_payment(ctx, B2BPaymentRequest(
            party_b="600000", amount_minor=100, command_id="BusinessPayBill",
            result_url="https://example.test/result", timeout_url="https://example.test/timeout"))),
        ("tax_remittance", lambda core: core.tax_remittance(ctx, TaxRemittanceRequest(
            prn="PRN-1", amount_minor=100, result_url="https://example.test/result",
            timeout_url="https://example.test/timeout"))),
        ("pull_register", lambda core: core.register_pull_transactions(ctx, PullTransactionsRegistrationRequest(
            nominated_phone_number="0712345678", callback_url="https://example.test/pull"))),
        ("pull_query", lambda core: core.pull_transactions(ctx, PullTransactionsRequest(
            start_at=now - timedelta(hours=1), end_at=now))),
        ("b2b_express", lambda core: core.b2b_express_checkout(ctx, B2BExpressCheckoutRequest(
            primary_shortcode="600111", receiver_shortcode="174379", amount_minor=100,
            reference="INV", partner_name="NetPay", callback_url="https://example.test/express",
            request_ref_id="ref-1"))),
        ("ratiba", lambda core: core.create_ratiba_order(ctx, RatibaStandingOrderRequest(
            standing_order_name="Plan-1", transaction_type="Standing Order Customer Pay Bill",
            amount_minor=100, phone_number="0712345678", callback_url="https://example.test/ratiba",
            account_reference="PLAN", description="Plan", frequency="5", start_date="20261029", end_date="20271029"))),
        ("bonga_quote", lambda core: core.calculate_lipa_na_bonga_value(ctx, LipaNaBongaQuoteRequest(bonga_points=400))),
        ("bonga_redeem", lambda core: core.redeem_lipa_na_bonga(ctx, LipaNaBongaRequest(
            phone_number="0712345678", amount_minor=100, bonga_points=5, account_reference="INV"))),
        ("bill_optin", lambda core: core.bill_manager_opt_in(ctx, BillManagerOptInRequest(
            email="billing@example.test", official_contact="0712345678", callback_url="https://example.test/bill"))),
        ("bill_single", lambda core: core.bill_manager_single_invoice(ctx, invoice)),
        ("bill_bulk", lambda core: core.bill_manager_bulk_invoices(ctx, BillManagerBulkInvoiceRequest(invoices=[invoice]))),
        ("bill_cancel", lambda core: core.bill_manager_cancel_invoice(ctx, BillManagerCancelInvoiceRequest(external_reference="INV-X"))),
        ("bill_cancel_bulk", lambda core: core.bill_manager_cancel_bulk_invoices(ctx, BillManagerBulkCancelInvoiceRequest(external_references=["INV-X"]))),
        ("bill_reconcile", lambda core: core.bill_manager_reconcile_payment(ctx, BillManagerReconciliationRequest(
            external_reference="INV-X", transaction_id="QAB123", amount_minor=100))),
        ("bill_update_optin", lambda core: core.bill_manager_update_opt_in(ctx, BillManagerOptInRequest(
            email="billing@example.test", official_contact="0712345678", callback_url="https://example.test/bill"))),
        ("bill_update_single", lambda core: core.bill_manager_update_invoice(ctx, invoice)),
        ("bill_update_bulk", lambda core: core.bill_manager_update_bulk_invoices(ctx, BillManagerBulkInvoiceRequest(invoices=[invoice]))),
    ]


@pytest.mark.asyncio
async def test_every_typed_operation_normalizes_provider_rejection() -> None:
    ctx = context()
    for operation, invoke in all_operation_calls(ctx):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/v1/generate":
                return httpx.Response(200, json={"access_token": "test-token", "expires_in": 3600})
            return httpx.Response(400, json={"ResponseCode": "1", "ResponseDescription": "rejected"})
        core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ProviderRejected):
                await invoke(core)
        finally:
            await core.aclose()


@pytest.mark.asyncio
async def test_every_typed_operation_classifies_malformed_and_ambiguous_outcomes() -> None:
    ctx = context()
    for operation, invoke in all_operation_calls(ctx):
        for failure_mode in ("malformed", "timeout"):
            def handler(request: httpx.Request) -> httpx.Response:
                if request.url.path == "/oauth/v1/generate":
                    return httpx.Response(200, json={"access_token": "test-token", "expires_in": 3600})
                if failure_mode == "malformed":
                    return httpx.Response(200, content=b"not-json")
                raise httpx.ReadTimeout("timeout", request=request)
            core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
            try:
                expected = MalformedProviderResponse if failure_mode == "malformed" else AmbiguousOutcome
                with pytest.raises(expected):
                    await invoke(core)
            finally:
                await core.aclose()


@pytest.mark.asyncio
async def test_oauth_cache_isolated_by_environment_and_credential_identity() -> None:
    token_calls: list[str] = []
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            token_calls.append(request.url.host)
            return httpx.Response(200, json={"access_token": f"token-{len(token_calls)}", "expires_in": 3600})
        return httpx.Response(200, json={"ResponseCode": "0"})
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    base = context()
    rotated = base.model_copy(update={"credentials": DarajaCredentials(
        consumer_key=SecretStr("consumer-key-test"),
        consumer_secret=SecretStr("rotated-secret"),
        passkey=SecretStr("passkey-test"),
        initiator_name="test-initiator",
        security_credential=SecretStr("encrypted-security-credential-test"),
        credential_version=2,
    )})
    production = context(environment="production")
    try:
        first = await core._token(base)
        second = await core._token(rotated)
        third = await core._token(production)
        assert len({first, second, third}) == 3
        assert token_calls.count("sandbox.safaricom.co.ke") == 2
        assert token_calls.count("api.safaricom.co.ke") == 1
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_short_lived_oauth_token_is_not_reused_past_safety_margin() -> None:
    token_calls = 0
    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls
        token_calls += 1
        return httpx.Response(200, json={"access_token": f"short-token-{token_calls}", "expires_in": 1})
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    try:
        assert await core._token(context()) == "short-token-1"
        assert await core._token(context()) == "short-token-2"
        assert token_calls == 2
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_missing_passkey_or_initiator_credentials_fail_before_network_io() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    no_passkey = context().model_copy(update={"credentials": DarajaCredentials(
        consumer_key=SecretStr("consumer-key-test"), consumer_secret=SecretStr("consumer-secret-test"),
    )})
    no_initiator = context().model_copy(update={"credentials": DarajaCredentials(
        consumer_key=SecretStr("consumer-key-test"), consumer_secret=SecretStr("consumer-secret-test"),
        passkey=SecretStr("passkey-test"),
    )})
    try:
        with pytest.raises(MissingCredential, match="passkey"):
            await core.stk_push(no_passkey, STKPushRequest(
                phone_number="0712345678", amount_minor=100, account_reference="INV",
                description="Sale", callback_url="https://example.test/stk",
            ))
        with pytest.raises(MissingCredential, match="initiator name"):
            await core.account_balance(no_initiator, AccountBalanceRequest(
                result_url="https://example.test/result", timeout_url="https://example.test/timeout",
            ))
        assert seen == []
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_server_error_is_ambiguous_and_rate_limit_is_safe_to_retry() -> None:
    server_core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({
        "/mpesa/qrcode/v1/generate": httpx.Response(503, json={"errorCode": "TEMPORARY"}),
    })))
    try:
        with pytest.raises(AmbiguousOutcome) as error:
            await server_core.dynamic_qr(context(), DynamicQRRequest(
                merchant_name="Shop", reference="INV", amount_minor=100,
                transaction_code="PB", credit_party_identifier="174379",
            ))
        assert error.value.http_status == 503
    finally:
        await server_core.aclose()

    rate_limit_core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({
        "/mpesa/qrcode/v1/generate": httpx.Response(429, json={"errorCode": "RATE_LIMIT"}),
    })))
    try:
        with pytest.raises(ProviderRejected) as error:
            await rate_limit_core.dynamic_qr(context(), DynamicQRRequest(
                merchant_name="Shop", reference="INV", amount_minor=100,
                transaction_code="PB", credit_party_identifier="174379",
            ))
        from app.mpesa_core.errors import RetryDisposition
        assert error.value.http_status == 429
        assert error.value.retry_disposition is RetryDisposition.SAFE
    finally:
        await rate_limit_core.aclose()


@pytest.mark.asyncio
async def test_oauth_response_requires_expiry_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "token-without-expiry"})
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(OAuthError):
            await core._token(context())
    finally:
        await core.aclose()


def test_stk_request_requires_callback_url() -> None:
    with pytest.raises(ValidationError):
        STKPushRequest(
            phone_number="0712345678", amount_minor=100,
            account_reference="INV", description="Sale",
        )


@pytest.mark.asyncio
async def test_provisional_product_contracts_are_blocked_in_production() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    try:
        with pytest.raises(CapabilityDisabled, match="pending contract verification"):
            await core.bill_manager_opt_in(context(environment="production"), BillManagerOptInRequest(
                email="billing@example.test", official_contact="0712345678",
                callback_url="https://example.test/bill",
            ))
        assert seen == []
    finally:
        await core.aclose()


@pytest.mark.asyncio
async def test_b2b_command_variants_are_passed_without_silent_substitution() -> None:
    seen: list[httpx.Request] = []
    core = MpesaCore(settings(), transport=httpx.MockTransport(handler_for({}, seen)))
    commands = [
        "BusinessPayBill", "BusinessBuyGoods", "BusinessToBusinessTransfer",
        "BusinessTransferFromMMFToUtility", "BusinessTransferFromUtilityToMMF", "BusinessPayToBulk",
    ]
    try:
        for index, command in enumerate(commands):
            await core.b2b_payment(context(), B2BPaymentRequest(
                party_b="600000", amount_minor=100, command_id=command,
                result_url="https://example.test/result", timeout_url="https://example.test/timeout",
                account_reference=f"INV-{index}",
            ))
        bodies = [json.loads(r.content) for r in seen if r.url.path == "/mpesa/b2b/v1/paymentrequest"]
        assert [body["CommandID"] for body in bodies] == commands
    finally:
        await core.aclose()
