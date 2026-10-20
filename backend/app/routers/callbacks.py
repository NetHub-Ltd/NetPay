"""Public Daraja callbacks with strict correlation and idempotent state changes."""

import hashlib
import json
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


def _fingerprint(
    integration_id: str,
    checkout_id: str,
    merchant_request_id: str,
    result_code: int,
    receipt: str | None,
    amount: object,
    phone_hash: str,
) -> str:
    raw = f"{integration_id}|{checkout_id}|{merchant_request_id}|{result_code}|{receipt or ''}|{amount}|{phone_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_payload(
    checkout_id: str,
    merchant_request_id: str,
    result_code: int,
    metadata: dict[str, object],
) -> dict[str, object]:
    phone_value = metadata.get("PhoneNumber")
    phone = str(phone_value) if phone_value is not None else ""
    phone_hash = ""
    if phone:
        try:
            normalized_phone = normalize_ke_phone(phone)
            phone_hash = hashlib.sha256(normalized_phone.encode("utf-8")).hexdigest()
            phone = normalized_phone
        except InvalidPhoneNumber:
            phone_hash = ""
    return {
        "checkout_request_id": checkout_id[:120],
        "merchant_request_id": merchant_request_id[:120],
        "result_code": result_code,
        "receipt": str(metadata.get("MpesaReceiptNumber", ""))[:64],
        "amount": str(metadata.get("Amount", ""))[:32],
        "phone_last_four": phone[-4:] if phone else "",
        "phone_hash": phone_hash,
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
    safe = _safe_payload(checkout_id, merchant_request_id, result_code, values)
    fingerprint = _fingerprint(
        integration_id, checkout_id, merchant_request_id, result_code, receipt, safe.get("amount", ""), str(safe.get("phone_hash", ""))
    )
    duplicate_result = await session.exec(
        select(ProviderCallback).where(
            ProviderCallback.integration_id == integration.id,
            ProviderCallback.dedupe_fingerprint == fingerprint,
        )
    )
    if duplicate_result.first() is not None:
        return _ack()

    payment_result = await session.exec(
        select(Payment)
        .where(
            Payment.integration_id == integration.id,
            Payment.provider_checkout_request_id == checkout_id,
        )
        .with_for_update()
    )
    payment = payment_result.first()
    integration_pk = integration.id
    payment_pk = payment.id if payment is not None else None
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
        if payment.provider_merchant_request_id and payment.provider_merchant_request_id != merchant_request_id:
            record.processing_status = "discrepancy"
        elif result_code != 0:
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
                if payment.status == "succeeded" and payment.provider_receipt not in (None, receipt):
                    record.processing_status = "discrepancy"
                    changed = False
                else:
                    changed = apply_status(payment, "succeeded")
                if changed or (payment.status == "succeeded" and record.processing_status != "discrepancy"):
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
        # A concurrent duplicate callback or conflicting receipt may have won
        # a unique constraint. Preserve an unmatched discrepancy when this was
        # not merely a duplicate fingerprint.
        await session.rollback()
        duplicate_check = await session.exec(
            select(ProviderCallback).where(
                ProviderCallback.integration_id == integration_pk,
                ProviderCallback.dedupe_fingerprint == fingerprint,
            )
        )
        if duplicate_check.first() is None:
            discrepancy_record = ProviderCallback(
                integration_id=integration_pk,
                payment_id=payment_pk,
                callback_type="stk",
                dedupe_fingerprint=fingerprint,
                safe_payload=safe,
                processing_status="discrepancy",
                received_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
            )
            session.add(discrepancy_record)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
    return _ack()


@router.post("/c2b/confirmation/{integration_id}")
async def c2b_confirmation(
    integration_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Persist an opted-in C2B confirmation as a payment and durable event."""
    try:
        payload: object = await request.json()
    except ValueError:
        return _ack()
    if not isinstance(payload, dict):
        return _ack()

    integration_result = await session.exec(
        select(DarajaIntegration).where(DarajaIntegration.integration_id == integration_id)
    )
    integration = integration_result.first()
    if integration is None or not integration.c2b_enabled:
        return _ack()

    receipt_value = payload.get("TransID")
    shortcode_value = payload.get("BusinessShortCode")
    amount_value = payload.get("TransAmount")
    if not isinstance(receipt_value, (str, int)) or not isinstance(shortcode_value, (str, int)):
        return _ack()
    receipt = str(receipt_value).strip()
    shortcode = str(shortcode_value).strip()
    if not receipt or len(receipt) > 64:
        return _ack()
    if shortcode not in {integration.shortcode, integration.party_b_shortcode}:
        return _ack()
    try:
        amount_minor_decimal = Decimal(str(amount_value)) * Decimal(100)
        if amount_minor_decimal <= 0 or amount_minor_decimal != amount_minor_decimal.to_integral_value():
            return _ack()
        amount_minor = int(amount_minor_decimal)
    except (InvalidOperation, TypeError, ValueError):
        return _ack()

    bill_reference_value = payload.get("BillRefNumber")
    bill_reference = str(bill_reference_value).strip()[:100] if bill_reference_value is not None else receipt
    fingerprint = hashlib.sha256(
        f"{integration_id}|c2b|{receipt}|{amount_minor}|{shortcode}|{bill_reference}".encode("utf-8")
    ).hexdigest()
    existing_payment_result = await session.exec(
        select(Payment).where(
            Payment.integration_id == integration.id,
            Payment.provider_receipt == receipt,
        )
    )
    existing_payment = existing_payment_result.first()
    if existing_payment is not None:
        if existing_payment.amount_minor != amount_minor or existing_payment.client_reference != (bill_reference or receipt):
            discrepancy_record = ProviderCallback(
                integration_id=integration.id,
                payment_id=existing_payment.id,
                callback_type="c2b_confirmation",
                dedupe_fingerprint=fingerprint,
                safe_payload={
                    "receipt": receipt,
                    "amount_minor": amount_minor,
                    "business_shortcode": shortcode,
                    "bill_reference": bill_reference,
                },
                processing_status="discrepancy",
                received_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
            )
            session.add(discrepancy_record)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
        return _ack()

    existing_callback_result = await session.exec(
        select(ProviderCallback).where(
            ProviderCallback.integration_id == integration.id,
            ProviderCallback.dedupe_fingerprint == fingerprint,
        )
    )
    if existing_callback_result.first() is not None:
        return _ack()

    now = datetime.now(timezone.utc)
    integration_pk = integration.id
    payment = Payment(
        merchant_id=integration.merchant_id,
        integration_id=integration.id,
        client_reference=bill_reference or receipt,
        amount_minor=amount_minor,
        currency="KES",
        phone_number=None,
        payment_source="c2b",
        status="succeeded",
        provider_receipt=receipt,
        provider_result_code="0",
        provider_result_description="C2B confirmation notification received",
        completed_at=now,
        created_at=now,
        updated_at=now,
    )
    safe_payload = {
        "receipt": receipt,
        "amount_minor": amount_minor,
        "business_shortcode": shortcode,
        "bill_reference": bill_reference,
        "transaction_time": str(payload.get("TransTime", ""))[:20],
    }
    callback_record = ProviderCallback(
        integration_id=integration.id,
        payment_id=payment.id,
        callback_type="c2b_confirmation",
        dedupe_fingerprint=fingerprint,
        safe_payload=safe_payload,
        processing_status="processed",
        received_at=now,
        processed_at=now,
    )
    payment_pk = payment.id
    session.add(payment)
    session.add(callback_record)
    session.add(payment_event(payment, "payment.succeeded"))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        duplicate_check = await session.exec(
            select(ProviderCallback).where(
                ProviderCallback.integration_id == integration_pk,
                ProviderCallback.dedupe_fingerprint == fingerprint,
            )
        )
        if duplicate_check.first() is None:
            discrepancy_record = ProviderCallback(
                integration_id=integration_pk,
                payment_id=payment_pk,
                callback_type="c2b_confirmation",
                dedupe_fingerprint=fingerprint,
                safe_payload=safe_payload,
                processing_status="discrepancy",
                received_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
            )
            session.add(discrepancy_record)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
    return _ack()


@router.post("/c2b/validation/{integration_id}")
async def c2b_validation(
    integration_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Validate basic C2B fields; account-specific validation is not yet configurable."""
    try:
        payload: object = await request.json()
    except ValueError:
        return {"ResultCode": 1, "ResultDesc": "Invalid request"}
    if not isinstance(payload, dict):
        return {"ResultCode": 1, "ResultDesc": "Invalid request"}

    integration_result = await session.exec(
        select(DarajaIntegration).where(DarajaIntegration.integration_id == integration_id)
    )
    integration = integration_result.first()
    if integration is None or not integration.c2b_enabled:
        return {"ResultCode": 1, "ResultDesc": "C2B is not enabled"}

    shortcode = str(payload.get("BusinessShortCode", "")).strip()
    if shortcode not in {integration.shortcode, integration.party_b_shortcode}:
        return {"ResultCode": 1, "ResultDesc": "Shortcode mismatch"}
    try:
        amount = Decimal(str(payload.get("TransAmount")))
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError):
        return {"ResultCode": 1, "ResultDesc": "Invalid amount"}
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
