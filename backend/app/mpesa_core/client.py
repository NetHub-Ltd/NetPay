"""Typed Daraja client and internal M-Pesa Core facade."""
import base64
from datetime import UTC, datetime
from zoneinfo import ZoneInfo
from typing import Mapping
from uuid import UUID

import httpx
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.models.integrations import DarajaIntegration
from app.models.payments import Payment
from app.mpesa_core.audit import ProviderOperationAuditor, redact_metadata
from app.mpesa_core.credentials import (
    CredentialVault,
    IntegrationCredentials,
    build_callback_urls,
    generate_security_credential,
)
from app.mpesa_core.errors import (
    CapabilityDisabled,
    ConfigurationError,
    IdempotencyConflictError,
    IntegrationNotReady,
)
from app.mpesa_core.oauth import OAuthTokenProvider
from app.mpesa_core.schemas import (
    AccountBalanceRequest,
    B2BPaymentRequest,
    B2CPaymentRequest,
    C2BRegistrationRequest,
    DynamicQRRequest,
    OperationOutcome,
    OperationResult,
    PullTransactionsRequest,
    ReversalRequest,
    STKPushRequest,
    STKQueryRequest,
    TransactionStatusRequest,
)


class MpesaCore:
    """Single internal boundary for Daraja credentials, requests, and audit.

    This class never decides the canonical financial outcome of a payment.
    An accepted STK response means only that Daraja accepted the initiation.
    """

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        redis_client: Redis | None = None,
        http_client: httpx.AsyncClient | None = None,
        auditor: ProviderOperationAuditor | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.mpesa_http_timeout_seconds, connect=3.0)
        )
        if auditor is None:
            if session_factory is None:
                raise ConfigurationError("a database session factory is required for durable provider audit")
            auditor = ProviderOperationAuditor(session_factory)
        self._auditor = auditor
        self._vault = CredentialVault(settings)
        self._oauth = OAuthTokenProvider(settings, self._http, auditor, redis_client)

    async def aclose(self) -> None:
        """Close only the HTTP client owned by this Core instance."""
        if self._owns_http:
            await self._http.aclose()

    @staticmethod
    def _base_url(integration: DarajaIntegration) -> str:
        return (
            "https://api.safaricom.co.ke"
            if integration.environment == "production"
            else "https://sandbox.safaricom.co.ke"
        )

    @staticmethod
    def _amount_shillings(amount_minor: int) -> int:
        if amount_minor <= 0 or amount_minor % 100:
            raise ValueError("M-Pesa KES amounts must be positive whole shillings in minor units")
        return amount_minor // 100

    @staticmethod
    def _phone_number(value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if digits.startswith("0") and len(digits) == 10:
            digits = "254" + digits[1:]
        elif digits.startswith("7") and len(digits) == 9:
            digits = "254" + digits
        if len(digits) != 12 or not digits.startswith("2547") and not digits.startswith("2541"):
            raise ValueError("phone_number must be a Kenyan M-Pesa mobile number")
        return digits

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%Y%m%d%H%M%S")

    def _ready(self, integration: DarajaIntegration, capability: str) -> IntegrationCredentials:
        if integration.status != "active" or integration.credential_status != "valid":
            raise IntegrationNotReady("Daraja integration must be active with validated credentials")
        capabilities = set(integration.enabled_capabilities or [])
        if capability not in capabilities:
            raise CapabilityDisabled(f"Daraja capability {capability} is not enabled for this integration")
        return self._vault.resolve(integration)

    async def validate_credentials(self, integration: DarajaIntegration) -> bool:
        """Verify consumer credentials with OAuth and persist validated integration state."""
        integration = await self.ensure_callback_urls(integration)
        credentials = self._vault.resolve(integration)
        await self._oauth.get_token(integration, credentials)
        integration.credential_status = "valid"
        integration.credentials_validated_at = datetime.now(UTC)
        integration.status = "active"
        if self._session_factory is not None:
            async with self._session_factory() as session:
                stored = await session.get(DarajaIntegration, integration.id)
                if stored is not None:
                    stored.credential_status = "valid"
                    stored.credentials_validated_at = integration.credentials_validated_at
                    stored.status = "active"
                    session.add(stored)
                    await session.commit()
        return True

    async def ensure_callback_urls(self, integration: DarajaIntegration) -> DarajaIntegration:
        """Generate and persist stable NetPay callback URLs when absent."""
        if integration.stk_callback_url and integration.c2b_validation_url and integration.c2b_confirmation_url:
            return integration
        urls = build_callback_urls(self._settings, integration)
        integration.stk_callback_url, integration.c2b_validation_url, integration.c2b_confirmation_url = urls
        if self._session_factory is not None:
            async with self._session_factory() as session:
                stored = await session.get(DarajaIntegration, integration.id)
                if stored is not None:
                    stored.stk_callback_url, stored.c2b_validation_url, stored.c2b_confirmation_url = urls
                    session.add(stored)
                    await session.commit()
                    await session.refresh(stored)
                    return stored
        return integration

    def _operation_callback_url(self, integration: DarajaIntegration, operation: str) -> str:
        """Build a dedicated result URL for asynchronous non-STK operations."""
        from urllib.parse import urlsplit

        base = (self._settings.mpesa_public_base_url or "").rstrip("/")
        parsed = urlsplit(base)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ConfigurationError("MPESA_PUBLIC_BASE_URL must be an absolute origin or base URL")
        if integration.environment == "production" and parsed.scheme != "https":
            raise ConfigurationError("production M-Pesa callback URLs must use HTTPS")
        if parsed.username or parsed.password:
            raise ConfigurationError("MPESA_PUBLIC_BASE_URL must not contain credentials")
        return f"{base}/callbacks/mpesa/{operation}/{integration.integration_id}"

    @staticmethod
    def _security_credential(
        integration: DarajaIntegration,
        credentials: IntegrationCredentials,
        settings: Settings,
    ) -> str:
        return generate_security_credential(integration, credentials, settings)

    @staticmethod
    def _provider_id(data: Mapping[str, object]) -> str | None:
        for key in (
            "CheckoutRequestID", "MerchantRequestID", "RequestID",
            "OriginatorConversationID", "ConversationID", "TransactionID",
        ):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _safe_response(data: Mapping[str, object]) -> dict[str, object]:
        allowed = {
            "ResponseCode", "ResponseDescription", "ResultCode", "ResultDesc",
            "CheckoutRequestID", "MerchantRequestID", "RequestID",
            "OriginatorConversationID", "ConversationID", "TransactionID",
            "errorCode", "errorMessage",
        }
        return redact_metadata({key: value for key, value in data.items() if key in allowed})

    async def _execute(
        self,
        integration: DarajaIntegration,
        *,
        capability: str,
        operation: str,
        path: str,
        payload: dict[str, object],
        idempotency_key: str | None = None,
        payment_id: UUID | None = None,
        payment_attempt_id: UUID | None = None,
        qr_response: bool = False,
    ) -> OperationResult:
        if idempotency_key is not None and (
            not idempotency_key.strip() or len(idempotency_key) > 160
        ):
            raise ValueError("idempotency_key must contain 1 to 160 non-whitespace characters")
        credentials = self._ready(integration, capability)
        token = await self._oauth.get_token(integration, credentials)
        audit = await self._auditor.start(
            integration,
            operation,
            payload,
            payment_id=payment_id,
            payment_attempt_id=payment_attempt_id,
            idempotency_key=idempotency_key,
        )
        if getattr(audit, "_idempotency_reused", False):
            try:
                prior_outcome = OperationOutcome(audit.outcome)
            except ValueError:
                prior_outcome = OperationOutcome.UNKNOWN
            if prior_outcome is OperationOutcome.ACCEPTED and operation == "stk_push":
                if not audit.provider_request_id:
                    prior_outcome = OperationOutcome.UNKNOWN
            prior_metadata = audit.response_metadata or {}
            logger.bind(
                operation=operation,
                correlation_id=str(audit.correlation_id),
                integration_id=integration.integration_id,
                outcome=prior_outcome.value,
            ).info("mpesa_idempotent_replay")
            prior_code = prior_metadata.get("ResponseCode", prior_metadata.get("ResultCode"))
            prior_description = prior_metadata.get("ResponseDescription", prior_metadata.get("ResultDesc"))
            return OperationResult(
                operation=operation,
                outcome=prior_outcome,
                correlation_id=audit.correlation_id,
                http_status=audit.http_status,
                provider_request_id=audit.provider_request_id,
                provider_code=str(prior_code) if prior_code is not None else None,
                provider_description=str(prior_description) if prior_description is not None else None,
                data=redact_metadata(prior_metadata),
            )
        try:
            response = await self._http.post(
                self._base_url(integration) + path,
                json=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=self._settings.mpesa_http_timeout_seconds,
            )
        except httpx.ConnectError:
            await self._auditor.finish(
                audit.id, outcome="not_sent", response_metadata={"error_code": "connect_error"}
            )
            logger.warning("mpesa_operation_not_sent operation={} correlation_id={}", operation, str(audit.correlation_id))
            return OperationResult(
                operation=operation, outcome=OperationOutcome.NOT_SENT, correlation_id=audit.correlation_id
            )
        except httpx.TimeoutException:
            await self._auditor.finish(
                audit.id, outcome="unknown", response_metadata={"error_code": "timeout"}
            )
            logger.warning("mpesa_operation_unknown operation={} correlation_id={} reason=timeout", operation, str(audit.correlation_id))
            return OperationResult(
                operation=operation, outcome=OperationOutcome.UNKNOWN, correlation_id=audit.correlation_id
            )
        except httpx.HTTPError as exc:
            await self._auditor.finish(
                audit.id, outcome="unknown", response_metadata={"error_code": type(exc).__name__}
            )
            logger.warning("mpesa_operation_unknown operation={} correlation_id={} reason=transport_error", operation, str(audit.correlation_id))
            return OperationResult(
                operation=operation, outcome=OperationOutcome.UNKNOWN, correlation_id=audit.correlation_id
            )

        try:
            decoded = response.json()
        except ValueError:
            await self._auditor.finish(
                audit.id,
                outcome="unknown",
                http_status=response.status_code,
                response_metadata={"error_code": "invalid_json"},
            )
            return OperationResult(
                operation=operation,
                outcome=OperationOutcome.UNKNOWN,
                correlation_id=audit.correlation_id,
                http_status=response.status_code,
            )
        data: dict[str, object] = decoded if isinstance(decoded, dict) else {}
        code_value = data.get("ResponseCode", data.get("ResultCode"))
        code = str(code_value) if code_value is not None else None
        description_value = data.get("ResponseDescription", data.get("ResultDesc", data.get("errorMessage")))
        description = str(description_value)[:500] if description_value is not None else None

        if response.status_code == 401:
            await self._oauth.invalidate(integration)
        if response.status_code >= 500:
            outcome = OperationOutcome.UNKNOWN
        elif response.status_code >= 400:
            outcome = OperationOutcome.REJECTED
        elif not data:
            outcome = OperationOutcome.UNKNOWN
        elif data.get("errorCode"):
            outcome = OperationOutcome.REJECTED
        elif qr_response and not isinstance(data.get("QRCode"), str):
            outcome = OperationOutcome.UNKNOWN
        elif operation == "stk_push" and not isinstance(data.get("CheckoutRequestID"), str):
            outcome = OperationOutcome.UNKNOWN
        elif code is None and self._provider_id(data) is None and not qr_response:
            outcome = OperationOutcome.UNKNOWN
        elif code is not None and code != "0" and not qr_response:
            outcome = OperationOutcome.REJECTED
        else:
            outcome = OperationOutcome.ACCEPTED

        await self._auditor.finish(
            audit.id,
            outcome=outcome.value,
            http_status=response.status_code,
            provider_request_id=self._provider_id(data),
            response_metadata=self._safe_response(data),
        )
        logger.bind(
            operation=operation,
            correlation_id=str(audit.correlation_id),
            integration_id=integration.integration_id,
            outcome=outcome.value,
            http_status=response.status_code,
        ).info("mpesa_provider_operation")
        return OperationResult(
            operation=operation,
            outcome=outcome,
            correlation_id=audit.correlation_id,
            http_status=response.status_code,
            provider_request_id=self._provider_id(data),
            provider_code=code,
            provider_description=description,
            data=redact_metadata(data),
        )

    async def stk_push(
        self,
        integration: DarajaIntegration,
        request: STKPushRequest,
        *,
        payment_id: UUID | None = None,
        payment_attempt_id: UUID | None = None,
        idempotency_key: str,
    ) -> OperationResult:
        """Initiate STK Push once per caller-supplied key; acceptance is not payment."""
        credentials = self._ready(integration, "stk_push")
        if not credentials.passkey:
            raise ConfigurationError("STK passkey is not configured")
        integration = await self.ensure_callback_urls(integration)
        shortcode = integration.shortcode
        if not shortcode:
            raise ConfigurationError("integration shortcode is required for STK Push")
        timestamp = self._timestamp()
        password = base64.b64encode(f"{shortcode}{credentials.passkey}{timestamp}".encode()).decode("ascii")
        transaction_type = "CustomerBuyGoodsOnline" if integration.product_type == "till" else "CustomerPayBillOnline"
        payload: dict[str, object] = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": self._amount_shillings(request.amount_minor),
            "PartyA": self._phone_number(request.phone_number),
            "PartyB": integration.party_b_shortcode or shortcode,
            "PhoneNumber": self._phone_number(request.phone_number),
            "CallBackURL": integration.stk_callback_url or "",
            "AccountReference": request.account_reference,
            "TransactionDesc": request.description,
        }
        return await self._execute(
            integration, capability="stk_push", operation="stk_push",
            path="/mpesa/stkpush/v1/processrequest", payload=payload,
            idempotency_key=idempotency_key,
            payment_id=payment_id, payment_attempt_id=payment_attempt_id,
        )

    async def stk_query(self, integration: DarajaIntegration, request: STKQueryRequest) -> OperationResult:
        """Query an STK request without interpreting the result as a financial ledger entry."""
        credentials = self._ready(integration, "stk_query")
        if not credentials.passkey or not integration.shortcode:
            raise ConfigurationError("STK passkey and shortcode are required")
        timestamp = self._timestamp()
        password = base64.b64encode(
            f"{integration.shortcode}{credentials.passkey}{timestamp}".encode()
        ).decode("ascii")
        return await self._execute(
            integration, capability="stk_query", operation="stk_query",
            path="/mpesa/stkpushquery/v1/query",
            payload={
                "BusinessShortCode": integration.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": request.checkout_request_id,
            },
        )

    async def register_c2b_urls(
        self, integration: DarajaIntegration, request: C2BRegistrationRequest, *, idempotency_key: str
    ) -> OperationResult:
        """Register URLs only after the merchant explicitly enables C2B."""
        if not integration.c2b_enabled:
            raise CapabilityDisabled("C2B registration is opt-in and is not enabled for this integration")
        integration = await self.ensure_callback_urls(integration)
        if not integration.shortcode:
            raise ConfigurationError("integration shortcode is required for C2B registration")
        result = await self._execute(
            integration, capability="c2b_registration", operation="c2b_register_url",
            path="/mpesa/c2b/v1/registerurl",
            idempotency_key=idempotency_key,
            payload={
                "ShortCode": integration.shortcode,
                "ResponseType": request.response_type,
                "ConfirmationURL": integration.c2b_confirmation_url or "",
                "ValidationURL": integration.c2b_validation_url or "",
            },
        )
        await self._persist_c2b_registration_result(integration, result)
        return result

    async def _persist_c2b_registration_result(
        self, integration: DarajaIntegration, result: OperationResult
    ) -> None:
        """Persist registration outcome without retrying ambiguous provider results."""
        if result.outcome is OperationOutcome.ACCEPTED:
            status = "registered"
            registered_at = datetime.now(UTC)
            error_code = None
        elif result.outcome is OperationOutcome.UNKNOWN:
            status = "unknown"
            registered_at = integration.c2b_registered_at
            error_code = "outcome_unknown"
        else:
            status = "failed"
            registered_at = integration.c2b_registered_at
            error_code = result.provider_code or result.outcome.value
        integration.c2b_registration_status = status
        integration.c2b_registered_at = registered_at
        integration.registration_error = error_code
        if self._session_factory is not None:
            try:
                async with self._session_factory() as session:
                    stored = await session.get(DarajaIntegration, integration.id)
                    if stored is not None:
                        stored.c2b_registration_status = status
                        stored.c2b_registered_at = registered_at
                        stored.registration_error = error_code
                        session.add(stored)
                        await session.commit()
            except Exception as exc:
                logger.error(
                    "mpesa_c2b_registration_state_persist_failed integration_id={} error_type={}",
                    integration.integration_id, type(exc).__name__,
                )
                from app.mpesa_core.errors import AuditPersistenceError
                raise AuditPersistenceError("C2B registration outcome could not be durably persisted") from exc

    async def dynamic_qr(self, integration: DarajaIntegration, request: DynamicQRRequest) -> OperationResult:
        """Generate a Dynamic QR for a product/shortcode with the required permission."""
        return await self._execute(
            integration, capability="dynamic_qr", operation="dynamic_qr",
            path="/mpesa/qrcode/v1/generate",
            payload={
                "MerchantName": request.merchant_name,
                "RefNo": request.reference,
                "Amount": self._amount_shillings(request.amount_minor),
                "TrxCode": request.transaction_code,
                "CPI": request.credit_party_identifier,
                "Size": str(request.size),
            },
            qr_response=True,
        )

    async def transaction_status(
        self, integration: DarajaIntegration, request: TransactionStatusRequest
    ) -> OperationResult:
        """Submit an asynchronous transaction-status query for reconciliation."""
        credentials = self._ready(integration, "transaction_status")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for transaction status")
        urls = await self.ensure_callback_urls(integration)
        payload: dict[str, object] = {
            "Initiator": credentials.initiator_name,
            "SecurityCredential": self._security_credential(integration, credentials, self._settings),
            "CommandID": "TransactionStatusQuery",
            "PartyA": request.party_a or integration.shortcode or "",
            "IdentifierType": request.identifier_type,
            "ResultURL": self._operation_callback_url(integration, "transaction-status"),
            "QueueTimeOutURL": self._operation_callback_url(integration, "transaction-status"),
            "Remarks": request.remarks,
            "Occasion": request.occasion,
        }
        if request.transaction_id:
            payload["TransactionID"] = request.transaction_id
        if request.original_conversation_id:
            payload["OriginalConversationID"] = request.original_conversation_id
        return await self._execute(
            integration, capability="transaction_status", operation="transaction_status",
            path="/mpesa/transactionstatus/v1/query", payload=payload,
        )

    async def account_balance(self, integration: DarajaIntegration, request: AccountBalanceRequest) -> OperationResult:
        """Request an asynchronous balance result under a separately enabled capability."""
        credentials = self._ready(integration, "account_balance")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for account balance")
        urls = await self.ensure_callback_urls(integration)
        return await self._execute(
            integration, capability="account_balance", operation="account_balance",
            path="/mpesa/accountbalance/v1/query",
            payload={
                "Initiator": credentials.initiator_name,
                "SecurityCredential": self._security_credential(integration, credentials, self._settings),
                "CommandID": "AccountBalance",
                "PartyA": integration.shortcode or "",
                "IdentifierType": request.identifier_type,
                "Remarks": request.remarks,
                "QueueTimeOutURL": self._operation_callback_url(integration, "account-balance"),
                "ResultURL": self._operation_callback_url(integration, "account-balance"),
                "Occasion": request.occasion,
            },
        )

    async def reverse_transaction(
        self, integration: DarajaIntegration, request: ReversalRequest, *, idempotency_key: str
    ) -> OperationResult:
        """Request a reversal; caller must enforce separate authorization and policy."""
        credentials = self._ready(integration, "reversal")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for reversals")
        urls = await self.ensure_callback_urls(integration)
        return await self._execute(
            integration, capability="reversal", operation="reversal",
            path="/mpesa/reversal/v1/request",
            idempotency_key=idempotency_key,
            payload={
                "Initiator": credentials.initiator_name,
                "SecurityCredential": self._security_credential(integration, credentials, self._settings),
                "CommandID": "TransactionReversal",
                "TransactionID": request.transaction_id,
                "Amount": self._amount_shillings(request.amount_minor),
                "ReceiverParty": request.receiver_party,
                "RecieverIdentifierType": request.receiver_identifier_type,
                "ResultURL": self._operation_callback_url(integration, "reversal"),
                "QueueTimeOutURL": self._operation_callback_url(integration, "reversal"),
                "Remarks": request.remarks,
                "Occasion": request.occasion,
            },
        )

    async def b2c_payment(
        self, integration: DarajaIntegration, request: B2CPaymentRequest, *, idempotency_key: str
    ) -> OperationResult:
        """Submit a gated B2C disbursement; accepted is not proof of delivery."""
        credentials = self._ready(integration, "b2c")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for B2C")
        urls = await self.ensure_callback_urls(integration)
        return await self._execute(
            integration, capability="b2c", operation="b2c_payment",
            path="/mpesa/b2c/v3/paymentrequest",
            idempotency_key=idempotency_key,
            payload={
                "InitiatorName": credentials.initiator_name,
                "SecurityCredential": self._security_credential(integration, credentials, self._settings),
                "CommandID": request.command_id,
                "Amount": self._amount_shillings(request.amount_minor),
                "PartyA": integration.shortcode or "",
                "PartyB": self._phone_number(request.phone_number),
                "Remarks": request.remarks,
                "QueueTimeOutURL": self._operation_callback_url(integration, "b2c"),
                "ResultURL": self._operation_callback_url(integration, "b2c"),
                "Occasion": request.occasion,
            },
        )

    async def b2b_payment(
        self, integration: DarajaIntegration, request: B2BPaymentRequest, *, idempotency_key: str
    ) -> OperationResult:
        """Submit a gated B2B business paybill/buy-goods operation."""
        credentials = self._ready(integration, "b2b")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for B2B")
        urls = await self.ensure_callback_urls(integration)
        payload: dict[str, object] = {
            "Initiator": credentials.initiator_name,
            "SecurityCredential": self._security_credential(integration, credentials, self._settings),
            "CommandID": request.command_id,
            "SenderIdentifierType": request.sender_identifier_type,
            "RecieverIdentifierType": request.receiver_identifier_type,
            "Amount": self._amount_shillings(request.amount_minor),
            "PartyA": integration.shortcode or "",
            "PartyB": request.party_b,
            "Remarks": request.remarks,
            "QueueTimeOutURL": self._operation_callback_url(integration, "b2b"),
            "ResultURL": self._operation_callback_url(integration, "b2b"),
            "Occasion": request.occasion,
        }
        if request.account_reference:
            payload["AccountReference"] = request.account_reference
        return await self._execute(
            integration, capability="b2b", operation="b2b_payment",
            path="/mpesa/b2b/v1/paymentrequest", payload=payload, idempotency_key=idempotency_key,
        )

    async def pull_transactions(
        self, integration: DarajaIntegration, request: PullTransactionsRequest
    ) -> OperationResult:
        """Submit a bounded Pull Transactions query when the product is enabled."""
        credentials = self._ready(integration, "pull_transactions")
        if not credentials.initiator_name:
            raise ConfigurationError("API initiator name is required for Pull Transactions")
        urls = await self.ensure_callback_urls(integration)
        return await self._execute(
            integration, capability="pull_transactions", operation="pull_transactions",
            path="/mpesa/pulltransactions/v1/query",
            payload={
                "StartDate": request.start_date.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
                "EndDate": request.end_date.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
                "OffSet": request.offset,
                "ShortCode": integration.shortcode or "",
                "UserName": credentials.initiator_name,
                "SecurityCredential": self._security_credential(integration, credentials, self._settings),
                "AccountNumber": request.account_number,
                "ResultURL": self._operation_callback_url(integration, "pull-transactions"),
                "QueueTimeOutURL": self._operation_callback_url(integration, "pull-transactions"),
            },
        )
