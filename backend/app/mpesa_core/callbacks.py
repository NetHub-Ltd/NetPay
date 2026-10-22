"""Untrusted callback normalization, correlation, deduplication, and persistence."""
import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Mapping
from uuid import UUID

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.integrations import DarajaIntegration
from app.models.operations import AuditLog
from app.models.payments import Payment, ProviderCallback
from app.mpesa_core.errors import UnknownIntegration
from app.mpesa_core.schemas import CallbackReceipt


def callback_fingerprint(payload: Mapping[str, object]) -> str:
    """Hash a canonical representation; raw callback payloads are never logged."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _mask_phone(value: object) -> str | None:
    if value is None:
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    return f"***{digits[-4:]}" if digits else None


def normalize_stk_callback(payload: Mapping[str, object]) -> dict[str, object]:
    """Extract only stable, useful STK evidence from the documented callback shape."""
    body = payload.get("Body")
    callback = body.get("stkCallback") if isinstance(body, dict) else None
    if not isinstance(callback, dict):
        raise ValueError("STK callback must contain Body.stkCallback")
    merchant_request_id = callback.get("MerchantRequestID")
    checkout_request_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")
    if not isinstance(merchant_request_id, str) or not merchant_request_id:
        raise ValueError("STK callback MerchantRequestID is required")
    if not isinstance(checkout_request_id, str) or not checkout_request_id:
        raise ValueError("STK callback CheckoutRequestID is required")
    if not isinstance(result_code, (int, str)) or str(result_code) not in {"0", "1"} and not str(result_code).isdigit():
        raise ValueError("STK callback ResultCode must be an integer")
    try:
        result_code_int = int(result_code)
    except (ValueError, TypeError) as exc:
        raise ValueError("STK callback ResultCode must be an integer") from exc

    amount: str | None = None
    receipt: str | None = None
    transaction_date: str | None = None
    phone: str | None = None
    metadata = callback.get("CallbackMetadata")
    if isinstance(metadata, dict):
        items = metadata.get("Item")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("Name")
                value = item.get("Value")
                if name == "Amount" and value is not None:
                    amount = str(value)
                elif name == "MpesaReceiptNumber" and value is not None:
                    receipt = str(value)[:64]
                elif name == "TransactionDate" and value is not None:
                    transaction_date = str(value)[:32]
                elif name == "PhoneNumber" and value is not None:
                    phone = str(value)
    safe: dict[str, object] = {
        "MerchantRequestID": merchant_request_id[:120],
        "CheckoutRequestID": checkout_request_id[:120],
        "ResultCode": result_code_int,
        "ResultDesc": str(callback.get("ResultDesc", ""))[:250],
        "phone_masked": _mask_phone(phone),
    }
    if amount is not None:
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError("STK callback amount must be positive")
            safe["Amount"] = str(amount_decimal)
        except InvalidOperation as exc:
            raise ValueError("STK callback amount is invalid") from exc
    if receipt:
        safe["MpesaReceiptNumber"] = receipt
    if transaction_date:
        safe["TransactionDate"] = transaction_date
    return {
        "provider_event_id": f"stk:{checkout_request_id}"[:120],
        "merchant_request_id": merchant_request_id,
        "checkout_request_id": checkout_request_id,
        "result_code": result_code_int,
        "receipt_number": receipt,
        "amount": amount,
        "phone_number": phone,
        "safe_payload": safe,
        "fingerprint": callback_fingerprint(payload),
    }


def _normalize_other_callback(
    callback_type: str, payload: Mapping[str, object]
) -> dict[str, object]:
    """Normalize asynchronous result callbacks without retaining arbitrary payloads."""
    fingerprint = callback_fingerprint(payload)
    result = payload.get("Result")
    result_data = result if isinstance(result, dict) else payload
    event_id = (
        result_data.get("OriginatorConversationID")
        or result_data.get("ConversationID")
        or result_data.get("TransactionID")
        or payload.get("TransID")
        or fingerprint
    )
    allowed = {
        "ResultType", "ResultCode", "ResultDesc", "OriginatorConversationID",
        "ConversationID", "TransactionID", "TransID", "TransAmount",
        "BusinessShortCode", "BillRefNumber", "TransTime", "ResponseCode",
    }
    safe = {key: value for key, value in result_data.items() if key in allowed}
    if "MSISDN" in result_data:
        safe["phone_masked"] = _mask_phone(result_data["MSISDN"])
    if "PhoneNumber" in result_data:
        safe["phone_masked"] = _mask_phone(result_data["PhoneNumber"])
    return {
        "provider_event_id": f"{callback_type}:{str(event_id)}"[:120],
        "safe_payload": safe,
        "fingerprint": fingerprint,
        "result_code": result_data.get("ResultCode", result_data.get("ResponseCode")),
    }


async def record_callback(
    session_factory: async_sessionmaker[AsyncSession],
    integration_id: str,
    callback_type: str,
    payload: Mapping[str, object],
) -> CallbackReceipt:
    """Persist minimized callback evidence once and correlate it to known records.

    This records provider evidence only. It intentionally does not mutate the
    canonical payment state; the payment domain owns state transitions and ledger
    effects. A duplicate event with conflicting contents is recorded as a separate
    audit discrepancy after the uniqueness conflict is rolled back.
    """
    if callback_type not in {
        "stk", "c2b_confirmation", "c2b_validation", "transaction_status",
        "account_balance", "reversal", "b2c", "b2b", "pull_transactions",
    }:
        raise ValueError("unsupported callback type")
    fingerprint = callback_fingerprint(payload)
    normalized = (
        normalize_stk_callback(payload)
        if callback_type == "stk"
        else _normalize_other_callback(callback_type, payload)
    )
    validation_accepted: bool | None = None

    async with session_factory() as session:
        integration_result = await session.exec(
            select(DarajaIntegration).where(DarajaIntegration.integration_id == integration_id)
        )
        integration = integration_result.first()
        if integration is None:
            raise UnknownIntegration("callback integration was not found")
        integration_db_id = integration.id
        integration_merchant_id = integration.merchant_id
        integration_public_id = integration.integration_id

        safe_payload = dict(normalized["safe_payload"])
        processing_status = "received"
        payment_id: UUID | None = None
        if callback_type == "stk":
            checkout_id = str(normalized.get("checkout_request_id", ""))
            payment_result = await session.exec(
                select(Payment).where(
                    Payment.integration_id == integration_db_id,
                    Payment.provider_checkout_request_id == checkout_id,
                )
            )
            payment = payment_result.first()
            if payment is not None:
                payment_id = payment.id
                safe_payload["payment_correlation"] = "matched"
                if normalized.get("amount") is not None:
                    try:
                        amount_minor_decimal = Decimal(str(normalized["amount"])) * 100
                        if amount_minor_decimal != amount_minor_decimal.to_integral_value() or int(amount_minor_decimal) != payment.amount_minor:
                            processing_status = "discrepancy"
                    except (InvalidOperation, ValueError):
                        processing_status = "discrepancy"
            else:
                safe_payload["payment_correlation"] = "unmatched"
                processing_status = "unmatched"
            if int(normalized.get("result_code", 1)) == 0 and (
                normalized.get("amount") is None or normalized.get("receipt_number") is None
            ):
                processing_status = "discrepancy"
        elif callback_type.startswith("c2b_"):
            expected_shortcode = integration.shortcode
            received_shortcode = payload.get("BusinessShortCode") or payload.get("ShortCode")
            try:
                amount = Decimal(str(payload.get("TransAmount", "0")))
                amount_valid = amount > 0
            except (InvalidOperation, ValueError):
                amount_valid = False
            shortcode_valid = bool(expected_shortcode and str(received_shortcode) == expected_shortcode)
            validation_accepted = (
                callback_type == "c2b_validation"
                and integration.c2b_enabled
                and "c2b_validation" in set(integration.enabled_capabilities or [])
                and shortcode_valid
                and amount_valid
            )
            if not shortcode_valid or not amount_valid:
                processing_status = "discrepancy"
            elif callback_type == "c2b_validation" and not validation_accepted:
                processing_status = "validation_not_enabled"

        event_id = str(normalized.get("provider_event_id") or f"{callback_type}:{fingerprint}")[:120]
        row = ProviderCallback(
            integration_id=integration_db_id,
            provider_event_id=event_id,
            merchant_id=integration_merchant_id,
            payment_id=payment_id,
            callback_type=callback_type,
            dedupe_fingerprint=fingerprint,
            payload=safe_payload,
            processing_status=processing_status,
        )
        session.add(row)
        try:
            await session.commit()
            logger.info(
                "mpesa_callback_recorded callback_type={} integration_id={} status={}",
                callback_type, integration_public_id, processing_status,
            )
            return CallbackReceipt(
                status="recorded",
                integration_id=integration_id,
                callback_type=callback_type,
                validation_accepted=validation_accepted,
            )
        except IntegrityError:
            await session.rollback()
            existing_fingerprint = await session.exec(
                select(ProviderCallback).where(
                    ProviderCallback.integration_id == integration_db_id,
                    ProviderCallback.dedupe_fingerprint == fingerprint,
                )
            )
            if existing_fingerprint.first() is not None:
                return CallbackReceipt(
                    status="duplicate",
                    integration_id=integration_id,
                    callback_type=callback_type,
                    validation_accepted=validation_accepted,
                )
            existing_event = await session.exec(
                select(ProviderCallback).where(
                    ProviderCallback.integration_id == integration_db_id,
                    ProviderCallback.provider_event_id == event_id,
                )
            )
            prior = existing_event.first()
            if prior is None:
                raise
            session.add(
                AuditLog(
                    merchant_id=integration_merchant_id,
                    actor_type="provider",
                    actor_id=None,
                    action="mpesa.callback.duplicate_conflict",
                    resource_type="provider_callback",
                    resource_id=prior.id if prior else None,
                    metadata_json={
                        "callback_type": callback_type,
                        "event_id_hash": hashlib.sha256(event_id.encode()).hexdigest(),
                        "new_fingerprint": fingerprint,
                    },
                )
            )
            await session.commit()
            logger.warning(
                "mpesa_callback_conflict callback_type={} integration_id={}",
                callback_type, integration_public_id,
            )
            return CallbackReceipt(
                status="conflict",
                integration_id=integration_id,
                callback_type=callback_type,
                validation_accepted=False if callback_type == "c2b_validation" else None,
            )
