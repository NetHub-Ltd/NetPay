"""Merchant-scoped payment initiation and status API."""

import hashlib
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import MerchantPrincipal, require_scope
from app.crypto import decrypt_secret
from app.daraja.client import DarajaUnavailable, InvalidDarajaCredentials
from app.daraja.stk import Environment, ProductType, STKOutcomeUnknown, STKRequestRejected, initiate_stk_push
from app.db import get_session
from app.models import DarajaIntegration, IdempotencyRecord, Payment, PaymentAttempt, ProviderCallback
from app.payments.outbox import payment_event
from app.payments.phone import InvalidPhoneNumber, normalize_ke_phone
from app.payments.state import apply_status
from app.schemas import PaymentCreate, PaymentSummary

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def _request_hash(payload: PaymentCreate, normalized_phone: str) -> str:
    canonical = {
        "integration_id": payload.integration_id,
        "client_reference": payload.client_reference,
        "amount_minor": payload.amount_minor,
        "currency": payload.currency,
        "phone_number": normalized_phone,
        "description": payload.description,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def _existing_idempotent_payment(
    session: AsyncSession,
    merchant_id: UUID,
    key: str,
    request_hash: str,
) -> Payment | None:
    result = await session.exec(
        select(IdempotencyRecord).where(
            IdempotencyRecord.merchant_id == merchant_id,
            IdempotencyRecord.key == key,
        )
    )
    record = result.first()
    if record is None:
        return None
    if record.request_hash != request_hash:
        raise HTTPException(status_code=409, detail={"code": "idempotency_conflict", "message": "This idempotency key was already used with a different request"})
    if record.resource_id is None:
        raise HTTPException(status_code=409, detail={"code": "request_in_progress", "message": "A request with this idempotency key is still being processed"})
    payment = await session.get(Payment, record.resource_id)
    if payment is None:
        raise HTTPException(status_code=409, detail={"code": "idempotency_resource_missing", "message": "The previous request resource is unavailable; contact support"})
    return payment


async def _apply_early_callback(
    session: AsyncSession,
    integration: DarajaIntegration,
    payment: Payment,
    checkout_request_id: str,
) -> str | None:
    """Resolve a callback that arrived before the STK response was committed."""
    result = await session.exec(
        select(ProviderCallback).where(
            ProviderCallback.integration_id == integration.id,
            ProviderCallback.processing_status == "unmatched",
        ).order_by(ProviderCallback.received_at.asc())
    )
    event_type: str | None = None
    expected_phone_hash = hashlib.sha256(payment.phone_number.encode("utf-8")).hexdigest()
    for callback in result.all():
        safe = callback.safe_payload
        if safe.get("checkout_request_id") != checkout_request_id:
            continue
        callback.payment_id = payment.id
        try:
            result_code = int(safe.get("result_code", -1))
        except (TypeError, ValueError):
            callback.processing_status = "discrepancy"
            callback.processed_at = datetime.now(timezone.utc)
            continue

        if result_code != 0:
            if apply_status(payment, "failed"):
                payment.provider_result_code = str(result_code)[:32]
                event_type = "payment.failed"
            elif payment.status != "failed":
                callback.processing_status = "discrepancy"
                callback.processed_at = datetime.now(timezone.utc)
                continue
        else:
            try:
                amount_minor = Decimal(str(safe.get("amount"))) * Decimal(100)
                valid_amount = amount_minor == Decimal(payment.amount_minor)
            except (InvalidOperation, TypeError, ValueError):
                valid_amount = False
            valid_phone = safe.get("phone_hash") == expected_phone_hash
            receipt = str(safe.get("receipt") or "")
            if not valid_amount or not valid_phone or not receipt:
                if apply_status(payment, "unknown"):
                    event_type = "payment.unknown"
                callback.processing_status = "discrepancy"
                callback.processed_at = datetime.now(timezone.utc)
                continue
            if apply_status(payment, "succeeded"):
                payment.provider_receipt = receipt[:64]
                payment.provider_result_code = "0"
                payment.provider_result_description = "Provider callback confirmed payment"
                event_type = "payment.succeeded"
            elif payment.status != "succeeded":
                callback.processing_status = "discrepancy"
                callback.processed_at = datetime.now(timezone.utc)
                continue

        callback.processing_status = "processed"
        callback.processed_at = datetime.now(timezone.utc)
    return event_type


@router.post("/stk-push", response_model=PaymentSummary, status_code=status.HTTP_202_ACCEPTED)
async def create_stk_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
    principal: MerchantPrincipal = Depends(require_scope("payments:write")),
    session: AsyncSession = Depends(get_session),
) -> Payment:
    """Persist a payment intent before calling Daraja; never return paid on acceptance."""
    if payload.amount_minor < 100 or payload.amount_minor % 100 != 0:
        raise HTTPException(status_code=422, detail={"code": "invalid_amount", "message": "STK Push requires a whole KES amount of at least KES 1"})
    try:
        phone = normalize_ke_phone(payload.phone_number)
    except InvalidPhoneNumber as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_phone", "message": str(exc)}) from exc

    request_hash = _request_hash(payload, phone)
    existing_payment = await _existing_idempotent_payment(session, principal.merchant_id, idempotency_key, request_hash)
    if existing_payment is not None:
        return existing_payment

    integration_result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == payload.integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.credential_status == "oauth_validated",
        )
    )
    integration = integration_result.first()
    if integration is None:
        raise HTTPException(status_code=404, detail={"code": "integration_not_found", "message": "A usable integration was not found"})

    payment = Payment(
        merchant_id=principal.merchant_id,
        integration_id=integration.id,
        client_reference=payload.client_reference,
        amount_minor=payload.amount_minor,
        currency=payload.currency,
        phone_number=phone,
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    attempt = PaymentAttempt(payment_id=payment.id, attempt_number=1, outcome="submitting")
    idempotency = IdempotencyRecord(
        merchant_id=principal.merchant_id,
        key=idempotency_key,
        request_hash=request_hash,
        resource_id=payment.id,
        response_status=status.HTTP_202_ACCEPTED,
        created_at=datetime.now(timezone.utc),
    )
    session.add(payment)
    session.add(attempt)
    session.add(idempotency)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        duplicate = await _existing_idempotent_payment(session, principal.merchant_id, idempotency_key, request_hash)
        if duplicate is not None:
            return duplicate
        raise HTTPException(status_code=409, detail={"code": "payment_conflict", "message": "A payment with this reference already exists"}) from exc

    try:
        accepted = await initiate_stk_push(
            environment=cast(Environment, integration.environment),
            consumer_key=decrypt_secret(integration.consumer_key_ciphertext),
            consumer_secret=decrypt_secret(integration.consumer_secret_ciphertext),
            passkey=decrypt_secret(integration.passkey_ciphertext),
            business_shortcode=integration.shortcode,
            party_b_shortcode=integration.party_b_shortcode,
            product_type=cast(ProductType, integration.product_type),
            amount_kes=payload.amount_minor // 100,
            phone_number=phone,
            callback_url=integration.stk_callback_url,
            account_reference=payment.id.hex[:12].upper(),
            description=payload.description,
        )
    except STKOutcomeUnknown:
        payment.status = "unknown"
        attempt.outcome = "unknown"
        attempt.safe_error_code = "provider_outcome_unknown"
        event_type = "payment.unknown"
    except STKRequestRejected as exc:
        payment.status = "failed"
        payment.completed_at = datetime.now(timezone.utc)
        attempt.outcome = "rejected"
        attempt.provider_result_code = exc.result_code
        attempt.safe_error_code = "provider_rejected"
        event_type = "payment.failed"
    except (DarajaUnavailable, InvalidDarajaCredentials):
        # These errors happen during OAuth, before an STK request is submitted.
        payment.status = "failed"
        payment.completed_at = datetime.now(timezone.utc)
        attempt.outcome = "not_submitted"
        attempt.safe_error_code = "provider_authentication_unavailable"
        event_type = "payment.failed"
    else:
        payment.provider_checkout_request_id = accepted.checkout_request_id
        payment.provider_merchant_request_id = accepted.merchant_request_id
        payment.initiated_at = datetime.now(timezone.utc)
        payment.updated_at = datetime.now(timezone.utc)
        attempt.outcome = "accepted"
        attempt.provider_result_code = "0"
        attempt.updated_at = datetime.now(timezone.utc)
        event_type = await _apply_early_callback(session, integration, payment, accepted.checkout_request_id) or "payment.pending"

    payment.updated_at = datetime.now(timezone.utc)
    session.add(payment)
    session.add(attempt)
    session.add(payment_event(payment, event_type))
    await session.commit()
    await session.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentSummary)
async def get_payment(
    payment_id: UUID,
    principal: MerchantPrincipal = Depends(require_scope("payments:read")),
    session: AsyncSession = Depends(get_session),
) -> Payment:
    result = await session.exec(
        select(Payment).where(Payment.id == payment_id, Payment.merchant_id == principal.merchant_id)
    )
    payment = result.first()
    if payment is None:
        raise HTTPException(status_code=404, detail={"code": "payment_not_found", "message": "Payment not found"})
    return payment
