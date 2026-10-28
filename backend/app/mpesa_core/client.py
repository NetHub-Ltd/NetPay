"""Small asynchronous client for the documented Safaricom Daraja API surface."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import httpx
from loguru import logger
from pydantic import SecretStr

from app.mpesa_core.errors import (
    AmbiguousOutcome,
    CatalogueContractUnavailable,
    CapabilityDisabled,
    InvalidRequest,
    MalformedProviderResponse,
    MissingCredential,
    OAuthError,
    OperationOutcome,
    ProviderRejected,
    RetryDisposition,
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
    ProviderOperationResult,
    PullTransactionsRequest,
    ReversalRequest,
    STKPushRequest,
    STKQueryRequest,
    TaxRemittanceRequest,
    TransactionStatusRequest,
)
from app.mpesa_core.validation import normalize_ke_phone, require_capability, validate_callback_url, validate_context


_SANDBOX = "https://sandbox.safaricom.co.ke"
_PRODUCTION = "https://api.safaricom.co.ke"


class MpesaCore:
    """One reusable, app-scoped async Daraja client.

    Core accepts credentials resolved by the application and never accesses
    persistence. Its token cache is isolated by environment and credential
    identity/version. Business mutations are never blindly retried.
    """

    def __init__(
        self,
        settings: Any | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._settings = settings
        timeout = timeout_seconds or getattr(settings, "mpesa_http_timeout_seconds", 10.0)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(timeout, 5.0)),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            transport=transport,
        )
        self._tokens: dict[str, tuple[str, float]] = {}
        self._token_locks: dict[str, asyncio.Lock] = {}
        self._closed = False

    async def aclose(self) -> None:
        """Close the reusable HTTP connection pool and clear in-memory tokens."""
        if not self._closed:
            self._closed = True
            self._tokens.clear()
            self._token_locks.clear()
            await self._client.aclose()

    async def __aenter__(self) -> "MpesaCore":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    @staticmethod
    def _secret(value: SecretStr | None, field: str) -> str:
        if value is None or not value.get_secret_value():
            raise MissingCredential(f"required credential '{field}' is missing")
        return value.get_secret_value()

    @staticmethod
    def _base_url(context: IntegrationContext) -> str:
        return _SANDBOX if context.environment == "sandbox" else _PRODUCTION

    @staticmethod
    def _cache_key(context: IntegrationContext) -> str:
        credentials = context.credentials
        identity = "|".join(
            (
                context.environment,
                credentials.consumer_key.get_secret_value(),
                credentials.credential_version.__str__(),
            )
        )
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    async def _token(self, context: IntegrationContext) -> str:
        validate_context(context)
        key = self._cache_key(context)
        cached = self._tokens.get(key)
        now = asyncio.get_running_loop().time()
        if cached and cached[1] - 30 > now:
            return cached[0]
        lock = self._token_locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._tokens.get(key)
            now = asyncio.get_running_loop().time()
            if cached and cached[1] - 30 > now:
                return cached[0]
            consumer_key = self._secret(context.credentials.consumer_key, "consumer_key")
            consumer_secret = self._secret(context.credentials.consumer_secret, "consumer_secret")
            url = self._base_url(context) + "/oauth/v1/generate?grant_type=client_credentials"
            basic = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode("ascii")
            try:
                response = await self._client.get(url, headers={"Authorization": f"Basic {basic}"})
            except httpx.HTTPError as exc:
                logger.warning("daraja_oauth_transport_error environment={} error_type={}", context.environment, type(exc).__name__)
                raise OAuthError("Daraja authorization request failed") from None
            if response.status_code < 200 or response.status_code >= 300:
                logger.warning("daraja_oauth_rejected environment={} http_status={}", context.environment, response.status_code)
                raise OAuthError("Daraja authorization was rejected")
            try:
                body = response.json()
                token = body["access_token"]
                expires_in = int(body.get("expires_in", 3600))
                if not isinstance(token, str) or not token or expires_in <= 0:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise OAuthError("Daraja authorization response was invalid") from None
            self._tokens[key] = (token, now + expires_in)
            return token

    @staticmethod
    def _operation_key(context: IntegrationContext, operation: str) -> str:
        return f"{context.integration_id}:{operation}"

    def _require(self, context: IntegrationContext, capability: str) -> None:
        validate_context(context)
        if capability not in context.enabled_capabilities:
            raise CapabilityDisabled(f"capability '{capability}' is not enabled")
        if self._closed:
            raise InvalidRequest("mpesa_core client is closed")

    @staticmethod
    def _safe_ids(body: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
        return (
            _optional_str(body.get("RequestID") or body.get("CheckoutRequestID") or body.get("MerchantRequestID")),
            _optional_str(body.get("ConversationID")),
            _optional_str(body.get("OriginatorConversationID")),
        )

    async def _request(
        self,
        context: IntegrationContext,
        operation: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        query: dict[str, str] | None = None,
        asynchronous: bool = False,
    ) -> ProviderOperationResult:
        if self._closed:
            raise InvalidRequest("mpesa_core client is closed")
        token = await self._token(context)
        url = self._base_url(context) + path
        if query:
            url += "?" + urlencode(query)
        try:
            response = await self._client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            logger.warning("daraja_transport_not_sent operation={} environment={} integration={}", operation, context.environment, context.integration_id)
            raise TransportFailure("Daraja connection could not be established") from None
        except (httpx.TimeoutException, httpx.NetworkError):
            logger.warning("daraja_transport_unknown operation={} environment={} integration={}", operation, context.environment, context.integration_id)
            raise AmbiguousOutcome("Daraja outcome is unknown; reconcile before retrying") from None
        except httpx.HTTPError as exc:
            logger.warning("daraja_transport_error operation={} error_type={}", operation, type(exc).__name__)
            raise AmbiguousOutcome("Daraja outcome is unknown; reconcile before retrying") from None

        try:
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, TypeError):
            logger.warning("daraja_malformed_response operation={} http_status={}", operation, response.status_code)
            raise MalformedProviderResponse("Daraja returned an invalid response") from None

        if response.status_code < 200 or response.status_code >= 300:
            code = _optional_str(body.get("errorCode") or body.get("ResponseCode"))
            logger.warning("daraja_http_rejection operation={} http_status={} provider_code={}", operation, response.status_code, code)
            raise ProviderRejected("Daraja rejected the request", provider_code=code)
        code = _optional_str(body.get("ResponseCode"))
        if code is not None and code != "0":
            logger.info("daraja_operation_rejected operation={} provider_code={}", operation, code)
            raise ProviderRejected("Daraja rejected the operation", provider_code=code)

        request_id, conversation_id, originator_id = self._safe_ids(body)
        outcome = OperationOutcome.ACCEPTED if asynchronous or operation in {"stk_push", "stk_query", "dynamic_qr", "c2b_registration", "c2b_simulation"} else OperationOutcome.ACCEPTED
        logger.info(
            "daraja_operation_complete operation={} environment={} integration={} http_status={} outcome={}",
            operation, context.environment, context.integration_id, response.status_code, outcome.value,
        )
        return ProviderOperationResult(
            operation=operation,
            outcome=outcome,
            response=body,
            provider_request_id=request_id,
            conversation_id=conversation_id,
            originator_conversation_id=originator_id,
            http_status=response.status_code,
            retry_disposition=RetryDisposition.NEVER,
        )

    @staticmethod
    def _timestamp_password(context: IntegrationContext) -> tuple[str, str]:
        passkey = MpesaCore._secret(context.credentials.passkey, "passkey")
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{context.shortcode}{passkey}{timestamp}".encode()).decode("ascii")
        return password, timestamp

    def _callback(self, context: IntegrationContext, url: str | None) -> str:
        selected = url or getattr(self._settings, "mpesa_public_base_url", None)
        if not selected:
            raise InvalidRequest("callback URL is required")
        selected = validate_callback_url(selected, production=context.environment == "production")
        return selected

    async def stk_push(self, context: IntegrationContext, request: STKPushRequest) -> ProviderOperationResult:
        """Initiate STK Push; provider acceptance is not payment completion."""
        self._require(context, "stk_push")
        phone = normalize_ke_phone(request.phone_number)
        password, timestamp = self._timestamp_password(context)
        callback = self._callback(context, request.callback_url)
        amount = request.amount_minor // 100
        payload = {
            "BusinessShortCode": context.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": request.transaction_type,
            "Amount": amount,
            "PartyA": phone,
            "PartyB": context.party_b_shortcode or context.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback,
            "AccountReference": request.account_reference,
            "TransactionDesc": request.description,
        }
        return await self._request(context, "stk_push", "POST", "/mpesa/stkpush/v1/processrequest", payload)

    async def stk_query(self, context: IntegrationContext, request: STKQueryRequest) -> ProviderOperationResult:
        """Query STK request status without interpreting acceptance as payment."""
        self._require(context, "stk_query")
        password, timestamp = self._timestamp_password(context)
        payload = {
            "BusinessShortCode": context.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": request.checkout_request_id,
        }
        return await self._request(context, "stk_query", "POST", "/mpesa/stkpushquery/v1/query", payload)

    async def register_c2b_urls(self, context: IntegrationContext, request: C2BRegistrationRequest) -> ProviderOperationResult:
        """Register C2B URLs only when the application explicitly enables C2B."""
        self._require(context, "c2b_registration")
        validation = validate_callback_url(request.validation_url, production=context.environment == "production")
        confirmation = validate_callback_url(request.confirmation_url, production=context.environment == "production")
        payload = {"ShortCode": context.shortcode, "ResponseType": request.response_type,
                   "ConfirmationURL": confirmation, "ValidationURL": validation}
        return await self._request(context, "c2b_registration", "POST", "/mpesa/c2b/v1/registerurl", payload)

    async def simulate_c2b(self, context: IntegrationContext, request: C2BSimulationRequest) -> ProviderOperationResult:
        """Simulate a C2B payment in sandbox only."""
        self._require(context, "c2b_simulation")
        if context.environment != "sandbox":
            raise CapabilityDisabled("C2B simulation is sandbox-only")
        payload = {"ShortCode": context.shortcode, "CommandID": "CustomerPayBillOnline",
                   "Amount": request.amount_minor // 100, "Msisdn": normalize_ke_phone(request.phone_number),
                   "BillRefNumber": request.bill_reference}
        return await self._request(context, "c2b_simulation", "POST", "/mpesa/c2b/v1/simulate", payload)

    async def dynamic_qr(self, context: IntegrationContext, request: DynamicQRRequest) -> ProviderOperationResult:
        """Generate a Dynamic QR payload."""
        self._require(context, "dynamic_qr")
        payload = {"MerchantName": request.merchant_name, "RefNo": request.reference,
                   "Amount": request.amount_minor // 100, "TrxCode": request.transaction_code,
                   "CPI": request.credit_party_identifier, "Size": str(request.size)}
        return await self._request(context, "dynamic_qr", "POST", "/mpesa/qrcode/v1/generate", payload)

    def _initiator_payload(self, context: IntegrationContext) -> dict[str, str]:
        initiator = context.credentials.initiator_name
        security = context.credentials.security_credential
        if not initiator:
            raise MissingCredential("initiator name is required for this operation")
        if security is None or not security.get_secret_value():
            raise MissingCredential("security credential is required for this operation")
        return {"Initiator": initiator, "SecurityCredential": security.get_secret_value()}

    async def transaction_status(self, context: IntegrationContext, request: TransactionStatusRequest) -> ProviderOperationResult:
        """Request asynchronous transaction status verification."""
        self._require(context, "transaction_status")
        payload: dict[str, Any] = {
            **self._initiator_payload(context), "CommandID": "TransactionStatusQuery",
            "PartyA": context.shortcode, "IdentifierType": "4",
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "Remarks": request.remarks,
        }
        if request.transaction_id:
            payload["TransactionID"] = request.transaction_id
        if request.original_conversation_id:
            payload["OriginalConversationID"] = request.original_conversation_id
        if request.occasion:
            payload["Occasion"] = request.occasion
        return await self._request(context, "transaction_status", "POST", "/mpesa/transactionstatus/v1/query", payload, asynchronous=True)

    async def account_balance(self, context: IntegrationContext, request: AccountBalanceRequest) -> ProviderOperationResult:
        """Request asynchronous account balance evidence."""
        self._require(context, "account_balance")
        payload = {
            **self._initiator_payload(context), "CommandID": "AccountBalance",
            "PartyA": context.shortcode, "IdentifierType": "4",
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "Remarks": request.remarks,
        }
        return await self._request(context, "account_balance", "POST", "/mpesa/accountbalance/v1/query", payload, asynchronous=True)

    async def reverse_transaction(self, context: IntegrationContext, request: ReversalRequest) -> ProviderOperationResult:
        """Request a supported reversal; final outcome arrives asynchronously."""
        self._require(context, "reversal")
        payload = {
            **self._initiator_payload(context), "CommandID": "TransactionReversal",
            "TransactionID": request.transaction_id, "Amount": request.amount_minor // 100,
            "ReceiverParty": request.receiver_party, "RecieverIdentifierType": "4",
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "Remarks": request.remarks,
        }
        if request.occasion:
            payload["Occasion"] = request.occasion
        return await self._request(context, "reversal", "POST", "/mpesa/reversal/v1/request", payload, asynchronous=True)

    async def b2c_payment(self, context: IntegrationContext, request: B2CPaymentRequest) -> ProviderOperationResult:
        """Initiate a B2C disbursement; completion is reported asynchronously."""
        self._require(context, "b2c")
        payload = {
            **self._initiator_payload(context), "OriginatorConversationID": request.originator_conversation_id,
            "CommandID": request.command_id, "Amount": request.amount_minor // 100,
            "PartyA": context.shortcode, "PartyB": normalize_ke_phone(request.phone_number),
            "Remarks": request.remarks,
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
        }
        if request.occasion:
            payload["Occasion"] = request.occasion
        return await self._request(context, "b2c", "POST", "/mpesa/b2c/v3/paymentrequest", payload, asynchronous=True)

    async def b2b_payment(self, context: IntegrationContext, request: B2BPaymentRequest) -> ProviderOperationResult:
        """Initiate a permitted B2B command; command permissions are provider-side."""
        self._require(context, "b2b")
        payload: dict[str, Any] = {
            **self._initiator_payload(context), "CommandID": request.command_id,
            "SenderIdentifierType": "4", "RecieverIdentifierType": "4",
            "Amount": request.amount_minor // 100, "PartyA": context.shortcode,
            "PartyB": request.party_b, "Remarks": request.remarks,
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
        }
        if request.account_reference:
            payload["AccountReference"] = request.account_reference
        if request.occasion:
            payload["Occasion"] = request.occasion
        return await self._request(context, "b2b", "POST", "/mpesa/b2b/v1/paymentrequest", payload, asynchronous=True)

    async def tax_remittance(self, context: IntegrationContext, request: TaxRemittanceRequest) -> ProviderOperationResult:
        """Remit a KRA PRN using the documented B2B Tax Remittance product."""
        self._require(context, "tax_remittance")
        payload = {
            **self._initiator_payload(context), "CommandID": "PayTaxToKRA",
            "SenderIdentifierType": "4", "RecieverIdentifierType": "4",
            "Amount": request.amount_minor // 100, "PartyA": context.shortcode,
            "PartyB": "572572", "AccountReference": request.prn,
            "Remarks": request.remarks,
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
        }
        return await self._request(context, "tax_remittance", "POST", "/mpesa/b2b/v1/remittax", payload, asynchronous=True)

    async def pull_transactions(self, context: IntegrationContext, request: PullTransactionsRequest) -> ProviderOperationResult:
        """Fail closed until the current portal contract is verified.

        A route must not be guessed. The typed date-window request is retained
        while the exact endpoint, required fields and callback semantics are
        verified against current product documentation.
        """
        self._require(context, "pull_transactions")
        raise CatalogueContractUnavailable(
            "Pull Transactions endpoint contract must be verified from the current Daraja portal before sending requests"
        )

    async def catalogue_operation(self, context: IntegrationContext, operation: str, payload: dict[str, Any]) -> ProviderOperationResult:
        """Fail closed for proposed catalogue entries without a verified contract."""
        supported = {"bill_manager", "ratiba", "lipa_na_bonga", "b2b_express_checkout"}
        if operation not in supported:
            raise InvalidRequest("unknown catalogue operation")
        self._require(context, operation)
        # Do not send untyped arbitrary payloads to a guessed URL.
        raise CatalogueContractUnavailable(
            f"Daraja contract for '{operation}' is not verified; no provider request was sent"
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int)):
        return str(value)
    return None
