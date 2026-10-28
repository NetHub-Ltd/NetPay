"""Small asynchronous client for the documented Safaricom Daraja API surface."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from loguru import logger
from pydantic import SecretStr, ValidationError

from app.mpesa_core.errors import (
    AmbiguousOutcome,
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
    AsyncOperationResponse,
    BillManagerResponse,
    C2BRegistrationResponse,
    C2BSimulationResponse,
    B2BExpressCheckoutRequest,
    BillManagerBulkCancelInvoiceRequest,
    BillManagerBulkInvoiceRequest,
    BillManagerCancelInvoiceRequest,
    BillManagerInvoiceRequest,
    BillManagerOptInRequest,
    BillManagerReconciliationRequest,
    B2BPaymentRequest,
    B2CPaymentRequest,
    C2BRegistrationRequest,
    C2BSimulationRequest,
    DynamicQRRequest,
    DynamicQRResponse,
    IntegrationContext,
    LipaNaBongaResponse,
    LipaNaBongaQuoteRequest,
    LipaNaBongaRequest,
    ProviderOperationResult,
    PullTransactionsRegistrationRequest,
    PullTransactionsRequest,
    PullTransactionsResponse,
    RatibaStandingOrderRequest,
    ReversalRequest,
    STKPushRequest,
    STKPushResponse,
    STKQueryRequest,
    STKQueryResponse,
    TaxRemittanceRequest,
    TransactionStatusRequest,
)
from app.mpesa_core.validation import normalize_ke_phone, validate_callback_url, validate_context


_SANDBOX = "https://sandbox.safaricom.co.ke"
_PRODUCTION = "https://api.safaricom.co.ke"
_PROVISIONAL_CAPABILITIES = frozenset({"pull_transactions", "b2b_express_checkout", "ratiba", "lipa_na_bonga", "bill_manager"})


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
                expires_in = int(body["expires_in"])
                if not isinstance(token, str) or not token or expires_in <= 0:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise OAuthError("Daraja authorization response was invalid") from None
            self._tokens[key] = (token, now + expires_in)
            return token

    def _require(self, context: IntegrationContext, capability: str) -> None:
        validate_context(context)
        if capability not in context.enabled_capabilities:
            raise CapabilityDisabled(f"capability '{capability}' is not enabled")
        if context.environment == "production" and capability in _PROVISIONAL_CAPABILITIES:
            raise CapabilityDisabled(f"capability '{capability}' is gated from production pending contract verification")
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
    ) -> ProviderOperationResult:
        if self._closed:
            raise InvalidRequest("mpesa_core client is closed")
        token = await self._token(context)
        url = self._base_url(context) + path
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
            if len(response.content) > 1_000_000:
                raise ValueError
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, TypeError):
            logger.warning("daraja_malformed_response operation={} http_status={}", operation, response.status_code)
            raise MalformedProviderResponse("Daraja returned an invalid response") from None

        if response.status_code < 200 or response.status_code >= 300:
            code = _safe_provider_code(body.get("errorCode") or body.get("ResponseCode"))
            logger.warning("daraja_http_rejection operation={} http_status={} provider_code={}", operation, response.status_code, code)
            if response.status_code == 429:
                raise ProviderRejected(
                    "Daraja rate-limited the request", provider_code=code,
                    http_status=response.status_code, retry_disposition=RetryDisposition.SAFE,
                )
            if response.status_code == 408 or response.status_code >= 500:
                raise AmbiguousOutcome(
                    "Daraja returned a server error; reconcile before retrying",
                    provider_code=code, http_status=response.status_code,
                )
            raise ProviderRejected("Daraja rejected the request", provider_code=code, http_status=response.status_code)
        code = _safe_provider_code(body.get("ResponseCode"))
        if code is not None and code != "0":
            logger.info("daraja_operation_rejected operation={} provider_code={}", operation, code)
            raise ProviderRejected("Daraja rejected the operation", provider_code=code, http_status=response.status_code)

        if operation == "stk_push":
            response_schema = STKPushResponse
        elif operation == "stk_query":
            response_schema = STKQueryResponse
        elif operation == "c2b_registration":
            response_schema = C2BRegistrationResponse
        elif operation == "c2b_simulation":
            response_schema = C2BSimulationResponse
        elif operation == "dynamic_qr":
            response_schema = DynamicQRResponse
        elif operation == "pull_transactions":
            response_schema = PullTransactionsResponse
        elif operation.startswith("bill_manager"):
            response_schema = BillManagerResponse
        elif operation.startswith("lipa_na_bonga"):
            response_schema = LipaNaBongaResponse
        else:
            response_schema = AsyncOperationResponse
        try:
            body = response_schema.model_validate(body).model_dump(by_alias=True, exclude_none=True)
        except ValidationError:
            logger.warning("daraja_response_schema_invalid operation={} http_status={}", operation, response.status_code)
            raise MalformedProviderResponse("Daraja response did not match the operation schema") from None

        request_id, conversation_id, originator_id = self._safe_ids(body)
        outcome = OperationOutcome.ACCEPTED
        logger.info(
            "daraja_operation_complete operation={} environment={} integration={} http_status={} outcome={}",
            operation, context.environment, context.integration_id, response.status_code, outcome.value,
        )
        safe_operations = {"stk_query", "dynamic_qr", "transaction_status", "account_balance", "pull_transactions", "lipa_na_bonga_quote"}
        retry_disposition = RetryDisposition.SAFE if operation in safe_operations else RetryDisposition.NEVER
        return ProviderOperationResult(
            operation=operation,
            outcome=outcome,
            response=_redact_response(body),
            provider_request_id=request_id,
            conversation_id=conversation_id,
            originator_conversation_id=originator_id,
            http_status=response.status_code,
            retry_disposition=retry_disposition,
        )

    @staticmethod
    def _timestamp_password(context: IntegrationContext) -> tuple[str, str]:
        passkey = MpesaCore._secret(context.credentials.passkey, "passkey")
        timestamp = datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{context.shortcode}{passkey}{timestamp}".encode()).decode("ascii")
        return password, timestamp

    def _callback(self, context: IntegrationContext, url: str) -> str:
        selected = url
        if not selected:
            raise InvalidRequest("application-resolved callback URL is required")
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

    def _initiator_payload(self, context: IntegrationContext, *, field_name: str = "Initiator") -> dict[str, str]:
        """Resolve the initiator and create Daraja's RSA-encrypted credential when needed."""
        initiator = context.credentials.initiator_name
        if not initiator:
            raise MissingCredential("initiator name is required for this operation")
        security = context.credentials.security_credential
        if security is not None and security.get_secret_value():
            security_value = security.get_secret_value()
        else:
            password = self._secret(context.credentials.initiator_password, "initiator_password")
            setting_name = (
                "mpesa_sandbox_certificate_pem"
                if context.environment == "sandbox"
                else "mpesa_production_certificate_pem"
            )
            certificate_secret = getattr(self._settings, setting_name, None)
            certificate_pem = self._secret(certificate_secret, setting_name)
            try:
                certificate = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
                public_key = certificate.public_key()
                if not isinstance(public_key, rsa.RSAPublicKey):
                    raise ValueError("certificate key is not RSA")
                encrypted = public_key.encrypt(password.encode("utf-8"), padding.PKCS1v15())
                security_value = base64.b64encode(encrypted).decode("ascii")
            except (ValueError, TypeError):
                raise MissingCredential("Daraja credential encryption configuration is invalid") from None
        return {field_name: initiator, "SecurityCredential": security_value}

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
        return await self._request(context, "transaction_status", "POST", "/mpesa/transactionstatus/v1/query", payload)

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
        return await self._request(context, "account_balance", "POST", "/mpesa/accountbalance/v1/query", payload)

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
        return await self._request(context, "reversal", "POST", "/mpesa/reversal/v1/request", payload)

    async def b2c_payment(self, context: IntegrationContext, request: B2CPaymentRequest) -> ProviderOperationResult:
        """Initiate a B2C disbursement; completion is reported asynchronously."""
        self._require(context, "b2c")
        payload = {
            **self._initiator_payload(context, field_name="InitiatorName"),
            "CommandID": request.command_id, "Amount": request.amount_minor // 100,
            "PartyA": context.shortcode, "PartyB": normalize_ke_phone(request.phone_number),
            "Remarks": request.remarks,
            "QueueTimeOutURL": validate_callback_url(request.timeout_url, production=context.environment == "production"),
            "ResultURL": validate_callback_url(request.result_url, production=context.environment == "production"),
        }
        if request.occasion:
            payload["Occasion"] = request.occasion
        return await self._request(context, "b2c", "POST", "/mpesa/b2c/v3/paymentrequest", payload)

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
        return await self._request(context, "b2b", "POST", "/mpesa/b2b/v1/paymentrequest", payload)

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
        return await self._request(context, "tax_remittance", "POST", "/mpesa/b2b/v1/remittax", payload)

    async def register_pull_transactions(self, context: IntegrationContext, request: PullTransactionsRegistrationRequest) -> ProviderOperationResult:
        """Register the shortcode for missed-C2B transaction recovery."""
        self._require(context, "pull_transactions")
        payload = {"ShortCode": context.shortcode,
                   "NominatedNumber": normalize_ke_phone(request.nominated_phone_number),
                   "CallBackURL": validate_callback_url(request.callback_url, production=context.environment == "production")}
        return await self._request(context, "pull_transactions_register", "POST", "/pulltransactions/v1/register", payload)

    async def pull_transactions(self, context: IntegrationContext, request: PullTransactionsRequest) -> ProviderOperationResult:
        """Query the Pull Transactions reconciliation endpoint."""
        self._require(context, "pull_transactions")
        payload = {"ShortCode": context.shortcode,
                   "StartDate": request.start_at.astimezone(ZoneInfo("Africa/Nairobi")).strftime("%Y-%m-%d %H:%M:%S"),
                   "EndDate": request.end_at.astimezone(ZoneInfo("Africa/Nairobi")).strftime("%Y-%m-%d %H:%M:%S"),
                   "OffSetValue": "0"}
        return await self._request(context, "pull_transactions", "POST", "/pulltransactions/v1/query", payload)

    async def b2b_express_checkout(self, context: IntegrationContext, request: B2BExpressCheckoutRequest) -> ProviderOperationResult:
        """Trigger the B2B USSD checkout prompt for a paying merchant."""
        self._require(context, "b2b_express_checkout")
        payload = {"primaryShortCode": request.primary_shortcode,
                   "receiverShortCode": request.receiver_shortcode,
                   "amount": request.amount_minor // 100,
                   "reference": request.reference,
                   "partnerName": request.partner_name,
                   "callbackUrl": validate_callback_url(request.callback_url, production=context.environment == "production"),
                   "requestRefID": request.request_ref_id}
        return await self._request(context, "b2b_express_checkout", "POST", "/v1/ussdpush/get-msisdn", payload)

    async def create_ratiba_order(self, context: IntegrationContext, request: RatibaStandingOrderRequest) -> ProviderOperationResult:
        """Create a customer-authorized M-Pesa Ratiba standing order."""
        self._require(context, "ratiba")
        payload = {"StandingOrderName": request.standing_order_name,
                   "BusinessShortCode": context.shortcode,
                   "TransactionType": request.transaction_type,
                   "Amount": request.amount_minor // 100,
                   "PartyA": normalize_ke_phone(request.phone_number),
                   "ReceiverPartyIdentifierType": "4",
                   "CallBackURL": validate_callback_url(request.callback_url, production=context.environment == "production"),
                   "AccountReference": request.account_reference,
                   "TransactionDesc": request.description,
                   "Frequency": request.frequency,
                   "StartDate": request.start_date,
                   "EndDate": request.end_date}
        return await self._request(context, "ratiba", "POST", "/standingorder/v1/createStandingOrderExternal", payload)

    async def redeem_lipa_na_bonga(self, context: IntegrationContext, request: LipaNaBongaRequest) -> ProviderOperationResult:
        """Redeem Bonga points toward a Paybill payment; settlement arrives via C2B."""
        self._require(context, "lipa_na_bonga")
        payload = {"BusinessShortCode": context.shortcode,
                   "PhoneNumber": normalize_ke_phone(request.phone_number),
                   "Amount": request.amount_minor // 100,
                   "BongaPoints": request.bonga_points,
                   "AccountReference": request.account_reference}
        return await self._request(context, "lipa_na_bonga", "POST", "/v1/lipa/na/bonga/redeem-paybill", payload)

    async def bill_manager_opt_in(self, context: IntegrationContext, request: BillManagerOptInRequest) -> ProviderOperationResult:
        """Opt the integration shortcode into Bill Manager."""
        self._require(context, "bill_manager")
        payload: dict[str, Any] = {"ShortCode": context.shortcode,
                                   "Email": request.email,
                                   "OfficialContact": normalize_ke_phone(request.official_contact),
                                   "SendReminders": "1" if request.send_reminders else "0",
                                   "CallbackURL": validate_callback_url(request.callback_url, production=context.environment == "production")}
        if request.logo_url:
            payload["Logo"] = validate_callback_url(request.logo_url, production=context.environment == "production")
        return await self._request(context, "bill_manager_opt_in", "POST", "/v1/billmanager-invoice/optin", payload)

    async def bill_manager_single_invoice(self, context: IntegrationContext, request: BillManagerInvoiceRequest) -> ProviderOperationResult:
        """Send one typed Bill Manager invoice."""
        self._require(context, "bill_manager")
        items = [{"ItemName": item.item_name, "Amount": item.amount_minor // 100} for item in request.invoice_items]
        payload: dict[str, Any] = {"ExternalReference": request.external_reference,
                                   "BilledFullName": request.billed_full_name,
                                   "BilledPhoneNumber": normalize_ke_phone(request.billed_phone_number),
                                   "Amount": request.amount_minor // 100,
                                   "DueDate": request.due_date,
                                   "AccountReference": request.account_reference,
                                   "InvoiceName": request.invoice_name,
                                   "InvoiceItems": items}
        if request.billed_period:
            payload["BilledPeriod"] = request.billed_period
        return await self._request(context, "bill_manager_invoice", "POST", "/v1/billmanager-invoice/single-invoicing", payload)

    async def bill_manager_cancel_invoice(self, context: IntegrationContext, request: BillManagerCancelInvoiceRequest) -> ProviderOperationResult:
        """Cancel one Bill Manager invoice by its external reference."""
        self._require(context, "bill_manager")
        return await self._request(context, "bill_manager_cancel_invoice", "POST", "/v1/billmanager-invoice/cancel-single-invoice",
                                   {"ExternalReference": request.external_reference})

    async def bill_manager_reconcile_payment(self, context: IntegrationContext, request: BillManagerReconciliationRequest) -> ProviderOperationResult:
        """Reconcile a provider payment against a Bill Manager invoice."""
        self._require(context, "bill_manager")
        payload = {"ExternalReference": request.external_reference,
                   "TransactionID": request.transaction_id,
                   "Amount": request.amount_minor // 100}
        return await self._request(context, "bill_manager_reconciliation", "POST", "/v1/billmanager-invoice/reconciliation", payload)




    async def calculate_lipa_na_bonga_value(self, context: IntegrationContext, request: LipaNaBongaQuoteRequest) -> ProviderOperationResult:
        """Calculate the value of Bonga points before the customer redeems them."""
        self._require(context, "lipa_na_bonga")
        return await self._request(context, "lipa_na_bonga_quote", "POST", "/v1/lipa/na/bonga/calculate-points",
                                   {"BongaPoints": request.bonga_points})

    async def bill_manager_bulk_invoices(self, context: IntegrationContext, request: BillManagerBulkInvoiceRequest) -> ProviderOperationResult:
        """Send a bounded batch of typed Bill Manager invoices."""
        self._require(context, "bill_manager")
        invoices = [self._bill_manager_invoice_payload(item) for item in request.invoices]
        return await self._request(context, "bill_manager_bulk_invoice", "POST", "/v1/billmanager-invoice/bulk-invoicing",
                                   {"Invoices": invoices})

    async def bill_manager_cancel_bulk_invoices(self, context: IntegrationContext, request: BillManagerBulkCancelInvoiceRequest) -> ProviderOperationResult:
        """Cancel a bounded batch of Bill Manager invoices."""
        self._require(context, "bill_manager")
        return await self._request(context, "bill_manager_cancel_bulk", "POST", "/v1/billmanager-invoice/cancel-bulk-invoice",
                                   {"ExternalReferences": request.external_references})

    async def bill_manager_update_opt_in(self, context: IntegrationContext, request: BillManagerOptInRequest) -> ProviderOperationResult:
        """Update a shortcode's Bill Manager onboarding details."""
        self._require(context, "bill_manager")
        payload = {"ShortCode": context.shortcode, "Email": request.email,
                   "OfficialContact": normalize_ke_phone(request.official_contact),
                   "SendReminders": "1" if request.send_reminders else "0",
                   "CallbackURL": validate_callback_url(request.callback_url, production=context.environment == "production")}
        if request.logo_url:
            payload["Logo"] = validate_callback_url(request.logo_url, production=context.environment == "production")
        return await self._request(context, "bill_manager_update_opt_in", "POST", "/v1/billmanager-invoice/change-optin-details", payload)

    async def bill_manager_update_invoice(self, context: IntegrationContext, request: BillManagerInvoiceRequest) -> ProviderOperationResult:
        """Update one existing Bill Manager invoice."""
        self._require(context, "bill_manager")
        return await self._request(context, "bill_manager_update_invoice", "POST", "/v1/billmanager-invoice/change-invoice",
                                   self._bill_manager_invoice_payload(request))

    async def bill_manager_update_bulk_invoices(self, context: IntegrationContext, request: BillManagerBulkInvoiceRequest) -> ProviderOperationResult:
        """Update a bounded batch of existing Bill Manager invoices."""
        self._require(context, "bill_manager")
        invoices = [self._bill_manager_invoice_payload(item) for item in request.invoices]
        return await self._request(context, "bill_manager_update_bulk", "POST", "/v1/billmanager-invoice/change-invoices",
                                   {"Invoices": invoices})

    @staticmethod
    def _bill_manager_invoice_payload(request: BillManagerInvoiceRequest) -> dict[str, Any]:
        """Convert the typed invoice contract into the provider's field names."""
        payload: dict[str, Any] = {
            "ExternalReference": request.external_reference,
            "BilledFullName": request.billed_full_name,
            "BilledPhoneNumber": normalize_ke_phone(request.billed_phone_number),
            "Amount": request.amount_minor // 100,
            "DueDate": request.due_date,
            "AccountReference": request.account_reference,
            "InvoiceName": request.invoice_name,
            "InvoiceItems": [{"ItemName": item.item_name, "Amount": item.amount_minor // 100}
                             for item in request.invoice_items],
        }
        if request.billed_period:
            payload["BilledPeriod"] = request.billed_period
        return payload


_SENSITIVE_KEY = re.compile(r"(secret|password|token|authorization|passkey|credential)", re.IGNORECASE)
_PHONE_KEY = re.compile(r"(phone|msisdn|mobile)", re.IGNORECASE)
_SAFE_CODE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def _safe_provider_code(value: object) -> str | None:
    """Keep provider codes bounded and free of arbitrary echoed payload text."""
    candidate = _optional_str(value)
    if candidate is None:
        return None
    return candidate if _SAFE_CODE.fullmatch(candidate) else "untrusted_provider_code"


def _redact_response(value: Any, *, key: str = "") -> Any:
    """Redact secret-like keys and mask phone-number values in returned metadata."""
    if _SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact_response(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_response(item, key=key) for item in value]
    if isinstance(value, str) and _PHONE_KEY.search(key):
        digits = re.sub(r"\D", "", value)
        return f"***{digits[-4:]}" if len(digits) >= 4 else "[REDACTED]"
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int)):
        return str(value)
    return None
