"""Public Daraja callback intake; callbacks are evidence, not authentication."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.models.integrations import DarajaIntegration
from app.models.payments import Payment, ProviderCallback

router = APIRouter(prefix="/v1/callbacks", tags=["provider callbacks"])


class CallbackAck(BaseModel):
    """Minimal acknowledgement returned after callback evidence is durably handled."""

    ResultCode: int = 0
    ResultDesc: str = "Accepted"


def _string_or_none(value: object) -> str | None:
    """Convert provider scalar values to bounded strings without retaining arbitrary objects."""
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    result = str(value)
    return result[:120] if result else None


@router.post("/stk/{integration_id}", response_model=CallbackAck, summary="Receive Daraja STK callback")
async def receive_stk_callback(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> CallbackAck:
    """Persist minimized callback evidence and require provider verification for final state."""
    integration_result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == integration_id,
            DarajaIntegration.deleted_at.is_(None),
        )
    )
    integration = integration_result.first()
    if integration is None:
        raise HTTPException(status_code=404, detail="integration_not_found")

    body = payload.get("Body")
    callback = body.get("stkCallback") if isinstance(body, dict) else None
    if not isinstance(callback, dict):
        raise HTTPException(status_code=400, detail="invalid_callback_payload")

    raw_result_code = callback.get("ResultCode")
    if isinstance(raw_result_code, bool):
        raise HTTPException(status_code=400, detail="invalid_callback_result")
    try:
        result_code = int(raw_result_code)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid_callback_result") from None

    checkout_id = _string_or_none(callback.get("CheckoutRequestID"))
    merchant_request_id = _string_or_none(callback.get("MerchantRequestID"))
    if not checkout_id and not merchant_request_id:
        raise HTTPException(status_code=400, detail="callback_request_id_missing")

    amount: str | None = None
    receipt: str | None = None
    transaction_date: str | None = None
    callback_metadata = callback.get("CallbackMetadata")
    items = callback_metadata.get("Item") if isinstance(callback_metadata, dict) else None
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("Name")
            value = _string_or_none(item.get("Value"))
            if name == "Amount":
                amount = value
            elif name == "MpesaReceiptNumber":
                receipt = value[:64] if value else None
            elif name == "TransactionDate":
                transaction_date = value

    # Store only allow-listed evidence. Never persist the raw callback body,
    # customer phone number, balance, ResultDesc, or arbitrary provider fields.
    safe_payload: dict[str, str | int | None] = {
        "checkout_request_id": checkout_id,
        "merchant_request_id": merchant_request_id,
        "result_code": result_code,
        "amount": amount,
        "receipt": receipt,
        "transaction_date": transaction_date,
    }
    canonical = json.dumps(safe_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    fingerprint = hashlib.sha256(canonical).hexdigest()
    event_id = checkout_id or merchant_request_id or fingerprint

    duplicate_result = await session.exec(
        select(ProviderCallback).where(
            ProviderCallback.integration_id == integration.id,
            or_(
                ProviderCallback.provider_event_id == event_id,
                ProviderCallback.dedupe_fingerprint == fingerprint,
            ),
        )
    )
    if duplicate_result.first() is not None:
        return CallbackAck()

    payment_conditions = []
    if checkout_id:
        payment_conditions.append(Payment.provider_checkout_request_id == checkout_id)
    if merchant_request_id:
        payment_conditions.append(Payment.provider_merchant_request_id == merchant_request_id)
    payment_result = await session.exec(
        select(Payment).where(
            Payment.integration_id == integration.id,
            Payment.deleted_at.is_(None),
            or_(*payment_conditions),
        )
    )
    payment = payment_result.first()

    processing_status = "verification_required" if payment is not None else "unmatched"
    processing_error = "provider_verification_required" if payment is not None else "no_matching_payment"
    if payment is not None:
        if payment.status in {"succeeded", "failed", "cancelled"}:
            processing_status = "conflict"
            processing_error = "callback_conflicts_with_terminal_state"
        else:
            # Callback input is unauthenticated and cannot finalize money movement.
            payment.status = "unknown"
            payment.provider_result_code = str(result_code)[:32]
            payment.provider_result_description = "Callback received; provider verification required"

    record = ProviderCallback(
        integration_id=integration.id,
        provider_event_id=event_id,
        merchant_id=integration.merchant_id,
        payment_id=payment.id if payment is not None else None,
        callback_type="stk",
        dedupe_fingerprint=fingerprint,
        provider_transaction_id=receipt,
        payload=safe_payload,
        processing_status=processing_status,
        processing_error=processing_error,
    )
    session.add(record)
    try:
        await session.flush()
        await session.commit()
    except IntegrityError:
        # Concurrent duplicate delivery: uniqueness constraints make the first
        # persisted event authoritative. Do not apply a second state transition.
        await session.rollback()
    return CallbackAck()
