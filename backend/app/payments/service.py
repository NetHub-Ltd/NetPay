"""Application service for canonical payment transitions and durable events."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.events import EventOutbox
from app.models.integrations import DarajaIntegration
from app.models.merchants import AuditLog
from app.models.payments import Payment, ProviderCallback
from app.mpesa_core.errors import MpesaCoreError


class PaymentApplicationService:
    """Own payment state transitions and their transactionally coupled event records."""

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
        if receipt is not None:
            payment.provider_receipt = str(receipt)[:64]
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
        session.add(AuditLog(
            merchant_id=payment.merchant_id,
            actor_type="provider_callback",
            action="payment.callback_processed",
            resource_type="payment",
            resource_id=payment.id,
            metadata_json={"callback_id": str(callback_row.id), "result_code": result_code, "new_status": payment.status},
        ))
        return True
