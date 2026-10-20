"""Public Daraja callbacks with strict correlation and idempotent state changes."""

import hashlib
import json
import hashlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import DarajaIntegration, Payment, ProviderCallback
from app.payments.outbox import payment_event
from app.payments.phone import InvalidPhoneNumber, normalize_ke_phone
from app.payments.state import apply_status

router = APIRouter(prefix="/cb", tags=["provider-callbacks"])


def _ack() -> dict[str, object]:
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


def _callback_parts(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    body = payload.get("Body")
    if not isinstance(body, dict):
        return None
    callback = body.get("stkCallback")
    return callback if isinstance(callback, dict) else None


def _metadata(callback: dict[str, Any]) -> dict[str, object]:
    metadata = callback.get("CallbackMetadata")
    items = metadata.get("Item") if isinstance(metadata, dict) else None
    values: dict[str, object] = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("Name"), str) and "Value" in item:
                values[item["Name"]] = item["Value"]
    return values


def _fingerprint(integration_id: str, checkout_id: str, result_code: int, receipt: str | None) -> str:
    raw = f"{integration_id}|{checkout_id}|{result_code}|{receipt or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_payload(
    checkout_id: str,
    merchant_request_id: str,
    result_code: int,
    metadata: dict[str, object],
) -> dict[str, object]:
    phone_value = metadata.get("PhoneNumber")
    phone = str(phone_value) if phone_value is not None else ""
    return {
        "checkout_request_id": checkout_id[:120],
        "merchant_request_id": merchant_request_id[:120],
        "result_code": result_code,
        "receipt": str(metadata.get("MpesaReceiptNumber", ""))[:64],
        "amount": str(metadata.get("Amount", ""))[:32],
        "phone_last_four": phone[-4:] if phone else "",
        "phone_hash": hashlib.sha256(phone.encode("utf-8")).hexdigest() if phone else "",
    }


@router.post("/stk/{integration_id}")
async def stk_callback(
    integration_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Accept callback traffic; only correlated, consistent evidence changes a payment."""
    try:
        payload: object = await request.json()
    except (ValueError, json.JSONDecodeError):
        return _ack()
    callback = _callback_parts(payload)
    if callback is None:
        return _ack()

    checkout_id = callback.get("CheckoutRequestID")
    merchant_request_id = callback.get("MerchantRequestID")
    try:
        result_code = int(callback.get("ResultCode"))
    except (TypeError, ValueError):
        return _ack()
    if not isinstance(checkout_id, str) or not checkout_id or not isinstance(merchant_request_id, str):
        return _ack()

    integration_result = await session.exec(
        select(DarajaIntegration).where(DarajaIntegration.integration_id == integration_id)
    )
    integration = integration_result.first()
    if integration is None:
        # The endpoint is public by design; do not reveal which routing IDs exist.
        return _ack()

    values = _metadata(callback)
    receipt_value = values.get("MpesaReceiptNumber")
    receipt = str(receipt_value) if receipt_value is not None else None
    fingerprint = _fingerprint(integration_id, checkout_id, result_code, receipt)
    duplicate_result = await session.exec(
        select(ProviderCallback).where(
            ProviderCallback.integration_id == integration.id,
            ProviderCallback.dedupe_fingerprint == fingerprint,
        )
    )
    if duplicate_result.first() is not None:
        return _ack()

    safe = _safe_payload(checkout_id, merchant_request_id, result_code, values)
    payment_result = await session.exec(
        select(Payment)
        .where(
            Payment.integration_id == integration.id,
            Payment.provider_checkout_request_id == checkout_id,
        )
        .with_for_update()
    )
    payment = payment_result.first()
    record = ProviderCallback(
        integration_id=integration.id,
        payment_id=payment.id if payment is not None else None,
        callback_type="stk",
        dedupe_fingerprint=fingerprint,
        safe_payload=safe,
        processing_status="unmatched" if payment is None else "processed",
        received_at=datetime.now(timezone.utc),
        processed_at=datetime.now(timezone.utc) if payment is not None else None,
    )
    session.add(record)

    event_type: str | None = None
    if payment is not None:
        if result_code != 0:
            changed = apply_status(payment, "failed")
            if changed:
                payment.provider_result_code = str(result_code)[:32]
                result_desc = callback.get("ResultDesc")
                payment.provider_result_description = result_desc[:250] if isinstance(result_desc, str) else None
                event_type = "payment.failed"
            elif payment.status != "failed":
                record.processing_status = "discrepancy"
        else:
            discrepancy = False
            amount_value = values.get("Amount")
            try:
                amount_minor = Decimal(str(amount_value)) * Decimal(100)
                if amount_minor != Decimal(payment.amount_minor):
                    discrepancy = True
            except (InvalidOperation, TypeError, ValueError):
                discrepancy = True
            phone_value = values.get("PhoneNumber")
            try:
                callback_phone = normalize_ke_phone(str(phone_value))
                if callback_phone != payment.phone_number:
                    discrepancy = True
            except (InvalidPhoneNumber, TypeError):
                discrepancy = True
            if not receipt or discrepancy:
                record.processing_status = "discrepancy"
                if apply_status(payment, "unknown"):
                    event_type = "payment.unknown"
            else:
                changed = apply_status(payment, "succeeded")
                if changed or payment.status == "succeeded":
                    payment.provider_receipt = receipt
                    payment.provider_result_code = "0"
                    payment.provider_result_description = "Provider callback confirmed payment"
                    if changed:
                        event_type = "payment.succeeded"
                else:
                    record.processing_status = "discrepancy"
        payment.updated_at = datetime.now(timezone.utc)
        session.add(payment)
        if event_type is not None:
            session.add(payment_event(payment, event_type))

    try:
        await session.commit()
    except IntegrityError:
        # A concurrent duplicate callback may have won the unique constraint.
        await session.rollback()
    return _ack()
