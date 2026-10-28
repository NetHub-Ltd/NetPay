"""Application service for canonical payment transitions and durable events."""
from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.attempts import PaymentAttempt
from app.models.events import EventOutbox
from app.models.attempts import PaymentAttempt
from app.models.integrations import DarajaIntegration
from app.models.operations import AuditLog
from app.models.payments import IdempotencyRecord, Payment, ProviderCallback
from app.mpesa_core import DarajaCredentials, IntegrationContext
from app.mpesa_core.credentials import decrypt_credentials
from app.mpesa_core.errors import (
    AmbiguousOutcome, CredentialStorageError, MalformedProviderResponse,
    MpesaCoreError, ProviderRejected, TransportFailure,
)
from app.mpesa_core.schemas import STKPushRequest
from app.mpesa_core.validation import normalize_ke_phone
from app.payments.schemas import STKInitiation
from app.payments.security import Principal


class PaymentApplicationService:
    """Own payment state transitions and their transactionally coupled event records."""

    def __init__(self, session: AsyncSession, core: Any, principal: Principal) -> None:
        self.session = session
        self.core = core
        self.principal = principal

    @staticmethod
    def context_for_integration(row: DarajaIntegration) -> IntegrationContext:
        if not row.credentials_ciphertext:
            raise HTTPException(status_code=409, detail="integration_credentials_missing")
        try:
            raw = json.loads(decrypt_credentials(row.credentials_ciphertext))
            credentials = DarajaCredentials(
                consumer_key=SecretStr(raw["consumer_key"]),
                consumer_secret=SecretStr(raw["consumer_secret"]),
                passkey=SecretStr(raw["passkey"]),
                credential_version=row.credential_version,
            )
        except CredentialStorageError as exc:
            code = exc.code
            status_code = 503 if code.startswith("credential_encryption_") else 500
            raise HTTPException(status_code=status_code, detail=code) from None
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail="stored_credentials_invalid") from exc
        return IntegrationContext(
            integration_id=row.integration_id,
            environment=row.environment,
            shortcode=row.shortcode or "",
            product_type=row.product_type,
            party_b_shortcode=row.party_b_shortcode,
            enabled_capabilities=frozenset(row.enabled_capabilities),
            credentials=credentials,
        )

    async def initiate_stk(self, payload: STKInitiation, idempotency_key: str | None) -> Payment:
        """Persist idempotent provider evidence, call Core once, and record the outcome."""
        session = self.session
        principal = self.principal
        if not idempotency_key or not idempotency_key.strip() or len(idempotency_key) > 160:
            raise HTTPException(status_code=400, detail="valid_idempotency_key_required")
        try:
            phone = normalize_ke_phone(payload.phone_number)
        except MpesaCoreError as exc:
            raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
        integration = await session.scalar(select(DarajaIntegration).where(
            DarajaIntegration.integration_id == payload.integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.deleted_at.is_(None),
        ))
        if integration is None:
            raise HTTPException(status_code=404, detail="integration_not_found")
        if integration.status != "active" or integration.credential_status != "validated":
            raise HTTPException(status_code=409, detail="integration_not_active")
        if "stk_push" not in integration.enabled_capabilities:
            raise HTTPException(status_code=403, detail="stk_push_capability_disabled")
        # Resolve credentials before recording an operation; local keyring failures
        # must not leave a pending payment that never reached Daraja.
        context = self.context_for_integration(integration)
        canonical = {
            "integration_id": integration.integration_id,
            "phone_number": phone,
            "amount_minor": payload.amount_minor,
            "merchant_reference": payload.merchant_reference,
            "description": payload.description,
        }
        request_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        existing = await session.scalar(select(IdempotencyRecord).where(
            IdempotencyRecord.merchant_id == principal.merchant_id,
            IdempotencyRecord.key == idempotency_key,
        ))
        if existing is not None:
            if existing.request_hash != request_hash:
                raise HTTPException(status_code=409, detail="idempotency_key_reused_with_different_request")
            if existing.resource_id is None:
                raise HTTPException(status_code=409, detail="idempotent_operation_in_progress")
            payment = await session.get(Payment, existing.resource_id)
            if payment is None or payment.merchant_id != principal.merchant_id:
                raise HTTPException(status_code=409, detail="idempotency_resource_unavailable")
            return payment
    
        payment = Payment(
            merchant_id=principal.merchant_id,
            integration_id=integration.id,
            merchant_reference=payload.merchant_reference,
            amount_minor=payload.amount_minor,
            currency="KES",
            phone_number=phone,
            payment_source="stk",
            direction="inbound",
            description=payload.description,
            status="pending",
        )
        session.add(payment)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail="merchant_reference_already_exists") from None
        attempt = PaymentAttempt(payment_id=payment.id, attempt_number=1, status="started")
        provider_request = ProviderRequest(
            merchant_id=principal.merchant_id,
            integration_id=integration.id,
            payment_id=payment.id,
            payment_attempt_id=attempt.id,
            operation="stk_push",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            outcome="started",
            request_metadata={"amount_minor": payload.amount_minor, "phone_suffix": phone[-4:]},
        )
        idempotency = IdempotencyRecord(
            merchant_id=principal.merchant_id,
            client_id=principal.client_id,
            key=idempotency_key,
            request_hash=request_hash,
            resource_id=payment.id,
            response_status=202,
        )
        session.add_all([attempt, provider_request, idempotency, AuditLog(
            merchant_id=principal.merchant_id,
            actor_type="m2m_client",
            actor_id=principal.client_id,
            action="payment.stk_initiated",
            resource_type="payment",
            resource_id=payment.id,
            metadata_json={"integration_id": integration.integration_id, "amount_minor": payload.amount_minor, "correlation_id": str(provider_request.correlation_id)},
        )])
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing = await session.scalar(select(IdempotencyRecord).where(
                IdempotencyRecord.merchant_id == principal.merchant_id,
                IdempotencyRecord.key == idempotency_key,
            ))
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise HTTPException(status_code=409, detail="idempotency_key_reused_with_different_request") from None
                payment = await session.get(Payment, existing.resource_id) if existing.resource_id else None
                if payment is not None:
                    return payment
            raise HTTPException(status_code=409, detail="payment_request_conflict") from None
    
        try:
            result = await self.core.stk_push(
                context,
                STKPushRequest(
                    phone_number=phone,
                    amount_minor=payload.amount_minor,
                    account_reference=payment.id.hex[:12],
                    description=payload.description[:13],
                    callback_url=integration.stk_callback_url or "",
                    transaction_type="CustomerBuyGoodsOnline" if integration.product_type == "buygoods" else "CustomerPayBillOnline",
                ),
            )
            payment.provider_checkout_request_id = result.response.get("CheckoutRequestID")
            payment.provider_merchant_request_id = result.response.get("MerchantRequestID")
            payment.initiated_at = datetime.now(UTC)
            payment.status = "pending"
            attempt.status = "accepted"
            provider_request.outcome = result.outcome.value
            provider_request.http_status = result.http_status
            provider_request.provider_request_id = result.provider_request_id
            provider_request.response_metadata = {
                "provider_request_id": result.provider_request_id,
                "conversation_id": result.conversation_id,
                "outcome": result.outcome.value,
            }
            provider_request.completed_at = datetime.now(UTC)
            # A callback may have arrived while the provider response was in flight.
            unmatched = (await session.exec(select(ProviderCallback).where(
                ProviderCallback.integration_id == integration.id,
                ProviderCallback.processing_status == "unmatched",
            ))).all()
            for callback_row in unmatched:
                if callback_row.payload.get("checkout_request_id") == payment.provider_checkout_request_id:
                    await PaymentApplicationService.apply_stk_callback(session, integration, callback_row)
            await session.commit()
        except MpesaCoreError as exc:
            now = datetime.now(UTC)
            provider_request.outcome = "unknown" if isinstance(exc, (AmbiguousOutcome, MalformedProviderResponse)) else "not_sent" if isinstance(exc, TransportFailure) else "rejected"
            provider_request.response_metadata = {"error_code": exc.code, "http_status": getattr(exc, "http_status", None)}
            provider_request.completed_at = now
            attempt.error_code = exc.code
            attempt.safe_error_code = exc.code
            attempt.safe_error_message = exc.safe_message[:500]
            attempt.status = "unknown" if isinstance(exc, (AmbiguousOutcome, MalformedProviderResponse)) else "failed"
            if isinstance(exc, (AmbiguousOutcome, MalformedProviderResponse)):
                payment.status = "unknown"
            else:
                payment.status = "failed"
                payment.failed_at = now
                payment.completed_at = now
                PaymentApplicationService.add_event(session, payment, "payment.failed")
            await session.commit()
            if isinstance(exc, (AmbiguousOutcome, MalformedProviderResponse)):
                return payment
            if isinstance(exc, TransportFailure):
                raise HTTPException(status_code=502, detail={"code": exc.code, "message": "Provider connection failed before request transmission"}) from None
            if isinstance(exc, ProviderRejected):
                raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
            raise HTTPException(status_code=502, detail={"code": exc.code, "message": exc.safe_message}) from None
        return payment

    @staticmethod
    def add_event(session: AsyncSession, payment: Payment, event_type: str) -> None:
        """Add an outbox event in the same transaction as its payment transition."""
        session.add(EventOutbox(
            merchant_id=payment.merchant_id,
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type=event_type,
            schema_version=1,
            payload={
                "payment_id": str(payment.id),
                "merchant_reference": payment.merchant_reference,
                "amount_minor": payment.amount_minor,
                "currency": payment.currency,
                "status": payment.status,
            },
        ))
    
    
    @staticmethod
    async def apply_stk_callback(
        session: AsyncSession,
        integration: DarajaIntegration,
        callback_row: ProviderCallback,
    ) -> bool:
        """Apply callback evidence to a known payment; return whether state changed."""
        data = callback_row.payload
        payment = await session.scalar(select(Payment).where(
            Payment.integration_id == integration.id,
            Payment.provider_checkout_request_id == data.get("checkout_request_id"),
        ))
        if payment is None:
            callback_row.processing_status = "unmatched"
            callback_row.processing_error = "no_matching_checkout_request"
            return False
        if payment.merchant_id != integration.merchant_id:
            callback_row.processing_status = "rejected"
            callback_row.processing_error = "merchant_mismatch"
            return False
        metadata = data.get("metadata", {})
        amount = metadata.get("Amount")
        if amount is not None:
            try:
                if Decimal(str(amount)) * 100 != payment.amount_minor:
                    callback_row.processing_status = "rejected"
                    callback_row.processing_error = "amount_mismatch"
                    return False
            except (InvalidOperation, ValueError):
                callback_row.processing_status = "rejected"
                callback_row.processing_error = "invalid_callback_amount"
                return False
        callback_merchant_request_id = data.get("merchant_request_id")
        if callback_merchant_request_id and payment.provider_merchant_request_id and callback_merchant_request_id != payment.provider_merchant_request_id:
            callback_row.processing_status = "rejected"
            callback_row.processing_error = "merchant_request_id_mismatch"
            return False
        callback_phone_last4 = metadata.get("PhoneNumberLast4")
        if callback_phone_last4 is not None and str(callback_phone_last4) != (payment.phone_number or "")[-4:]:
            callback_row.processing_status = "rejected"
            callback_row.processing_error = "phone_mismatch"
            return False
    
        if payment.status in {"succeeded", "failed", "cancelled", "expired"}:
            callback_row.processing_status = "duplicate_or_terminal"
            callback_row.processed_at = datetime.now(UTC)
            return False
    
        result_code = int(data["result_code"])
        payment.provider_result_code = str(result_code)
        payment.provider_result_description = str(data.get("result_description", ""))[:250]
        receipt = metadata.get("MpesaReceiptNumber")
        if result_code == 0:
            if not receipt:
                callback_row.processing_status = "rejected"
                callback_row.processing_error = "successful_callback_missing_receipt"
                return False
            receipt_value = str(receipt)[:64]
            existing_receipt = await session.scalar(select(Payment).where(
                Payment.integration_id == integration.id,
                Payment.provider_receipt == receipt_value,
                Payment.id != payment.id,
            ))
            if existing_receipt is not None:
                callback_row.processing_status = "rejected"
                callback_row.processing_error = "provider_receipt_already_used"
                return False
            payment.provider_receipt = receipt_value
            payment.provider_transaction_id = str(receipt)[:120]
        now = datetime.now(UTC)
        if result_code == 0:
            if not payment.provider_receipt:
                callback_row.processing_status = "rejected"
                callback_row.processing_error = "successful_callback_missing_receipt"
                return False
            payment.status = "succeeded"
            payment.succeeded_at = now
            payment.completed_at = now
            PaymentApplicationService.add_event(session, payment, "payment.succeeded")
        else:
            payment.status = "failed"
            payment.failed_at = now
            payment.completed_at = now
            PaymentApplicationService.add_event(session, payment, "payment.failed")
        callback_row.payment_id = payment.id
        callback_row.merchant_id = payment.merchant_id
        callback_row.processing_status = "processed"
        callback_row.processing_error = None
        callback_row.processed_at = now
        attempt_result = await session.exec(select(PaymentAttempt).where(
            PaymentAttempt.payment_id == payment.id,
        ).order_by(PaymentAttempt.attempt_number.desc()))
        attempt = attempt_result.first()
        if attempt is not None:
            attempt.status = payment.status
            attempt.completed_at = now
            if payment.status == "failed":
                attempt.safe_error_code = str(result_code)
                attempt.safe_error_message = "Daraja callback reported payment failure"
            else:
                attempt.safe_error_code = None
                attempt.safe_error_message = None
            session.add(attempt)
        session.add(AuditLog(
            merchant_id=payment.merchant_id,
            actor_type="provider_callback",
            action="payment.callback_processed",
            resource_type="payment",
            resource_id=payment.id,
            metadata_json={"callback_id": str(callback_row.id), "result_code": result_code, "new_status": payment.status},
        ))
        return True
