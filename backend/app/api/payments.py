"""Merchant-scoped payment initiation and status lookup."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.credentials import CredentialEncryptionError, decrypt_credential
from app.core.database import get_session
from app.core.machine_auth import MachinePrincipal, require_scopes
from app.models.attempts import PaymentAttempt
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient
from app.models.operations import ProviderRequest
from app.models.payments import IdempotencyRecord, Payment
from app.providers.daraja import DarajaStkRejected, DarajaStkUncertain, initiate_stk_push

router = APIRouter(prefix="/v1/payments", tags=["payments"])


class PaymentCreateRequest(BaseModel):
    """A whole-KES amount and merchant reference for one STK payment intent."""

    integration_id: str = Field(min_length=8, max_length=64)
    merchant_reference: str = Field(min_length=1, max_length=120)
    amount_kes: int = Field(gt=0, le=250_000)
    phone_number: str = Field(min_length=9, max_length=16)
    description: str = Field(default="Payment", min_length=1, max_length=13)

    @field_validator("phone_number")
    @classmethod
    def normalize_kenyan_phone(cls, value: str) -> str:
        """Normalize common Kenyan mobile formats to Daraja's 254XXXXXXXXX form."""
        digits = re.sub(r"[\s()+-]", "", value)
        if digits.startswith("0") and len(digits) == 10:
            digits = "254" + digits[1:]
        if len(digits) == 12 and re.fullmatch(r"254[17]\d{8}", digits):
            return digits
        raise ValueError("phone_number must be a valid Kenyan mobile number")


class PaymentResponse(BaseModel):
    """Safe payment state; initiation acknowledgement is not payment success."""

    payment_id: UUID
    merchant_reference: str
    amount_minor: int
    currency: str
    status: str
    provider_checkout_request_id: str | None
    provider_merchant_request_id: str | None
    provider_receipt: str | None
    provider_result_code: str | None
    initiated_at: datetime | None
    completed_at: datetime | None


def _to_response(payment: Payment) -> PaymentResponse:
    """Map a payment to a stable response without internal provider payloads."""
    return PaymentResponse(
        payment_id=payment.id,
        merchant_reference=payment.merchant_reference,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        status=payment.status,
        provider_checkout_request_id=payment.provider_checkout_request_id,
        provider_merchant_request_id=payment.provider_merchant_request_id,
        provider_receipt=payment.provider_receipt,
        provider_result_code=payment.provider_result_code,
        initiated_at=payment.initiated_at,
        completed_at=payment.completed_at,
    )


def _request_hash(body: PaymentCreateRequest) -> str:
    """Hash canonical request data for merchant-scoped idempotency."""
    canonical = {
        "integration_id": body.integration_id,
        "merchant_reference": body.merchant_reference,
        "amount_kes": body.amount_kes,
        "phone_number": body.phone_number,
        "description": body.description,
    }
    raw = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def _existing_payment_for_idempotency(
    session: AsyncSession,
    *,
    merchant_id: UUID,
    key: str,
    request_hash: str,
) -> PaymentResponse | None:
    """Return the existing payment for an exact replay; reject key reuse with new data."""
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
        raise HTTPException(status_code=409, detail="idempotency_key_reused_with_different_request")
    if record.resource_id is None:
        raise HTTPException(status_code=409, detail="idempotent_request_in_progress")
    payment_result = await session.exec(
        select(Payment).where(
            Payment.id == record.resource_id,
            Payment.merchant_id == merchant_id,
        )
    )
    payment = payment_result.first()
    if payment is None:
        raise HTTPException(status_code=409, detail="idempotent_resource_unavailable")
    return _to_response(payment)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate an idempotent STK Push",
)
async def create_payment(
    body: PaymentCreateRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    principal: MachinePrincipal = Depends(require_scopes("payments:write")),
    session: AsyncSession = Depends(get_session),
) -> PaymentResponse:
    """Persist intent before provider I/O and never retry an ambiguous STK request."""
    request_hash = _request_hash(body)
    replay = await _existing_payment_for_idempotency(
        session,
        merchant_id=principal.merchant_id,
        key=idempotency_key,
        request_hash=request_hash,
    )
    if replay is not None:
        return replay

    integration_result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == body.integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.provider == "daraja",
            DarajaIntegration.status == "active",
            DarajaIntegration.credential_status == "valid",
            DarajaIntegration.deleted_at.is_(None),
        )
    )
    integration = integration_result.first()
    if integration is None:
        raise HTTPException(status_code=404, detail="integration_not_found")

    duplicate_reference_result = await session.exec(
        select(Payment).where(
            Payment.merchant_id == principal.merchant_id,
            Payment.merchant_reference == body.merchant_reference,
            Payment.deleted_at.is_(None),
        )
    )
    if duplicate_reference_result.first() is not None:
        raise HTTPException(status_code=409, detail="merchant_reference_already_used")

    client_result = await session.exec(
        select(M2MClient).where(
            M2MClient.client_id == principal.client_id,
            M2MClient.merchant_id == principal.merchant_id,
            M2MClient.status == "active",
            M2MClient.revoked_at.is_(None),
            M2MClient.deleted_at.is_(None),
        )
    )
    client = client_result.first()
    if client is None:
        raise HTTPException(status_code=401, detail="invalid_machine_credentials")

    settings = get_settings()
    if settings.credential_encryption_key is None or not settings.credential_encryption_key.get_secret_value():
        raise HTTPException(status_code=503, detail="credential_encryption_not_configured")
    try:
        consumer_key = decrypt_credential(integration.consumer_key_ciphertext or b"", key=settings.credential_encryption_key)
        consumer_secret = decrypt_credential(integration.consumer_secret_ciphertext or b"", key=settings.credential_encryption_key)
        passkey = decrypt_credential(integration.passkey_ciphertext or b"", key=settings.credential_encryption_key)
    except CredentialEncryptionError:
        raise HTTPException(status_code=503, detail="integration_credentials_unavailable") from None

    now = datetime.now(UTC)
    payment = Payment(
        merchant_id=principal.merchant_id,
        integration_id=integration.id,
        merchant_reference=body.merchant_reference,
        amount_minor=body.amount_kes * 100,
        currency="KES",
        phone_number=body.phone_number,
        payment_source="stk",
        direction="inbound",
        description=body.description,
        status="pending",
    )
    attempt = PaymentAttempt(payment_id=payment.id, attempt_number=1, status="started")
    provider_request = ProviderRequest(
        merchant_id=principal.merchant_id,
        integration_id=integration.id,
        payment_id=payment.id,
        payment_attempt_id=attempt.id,
        operation="stk_push",
        correlation_id=attempt.correlation_id,
        outcome="started",
        request_metadata={
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "environment": integration.environment,
            "product_type": integration.product_type or "paybill",
        },
        response_metadata={},
    )
    idempotency = IdempotencyRecord(
        merchant_id=principal.merchant_id,
        client_id=client.id,
        key=idempotency_key,
        request_hash=request_hash,
        resource_id=payment.id,
        response_status=status.HTTP_202_ACCEPTED,
    )
    session.add(payment)
    session.add(attempt)
    session.add(provider_request)
    session.add(idempotency)
    try:
        await session.flush()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        replay_after_race = await _existing_payment_for_idempotency(
            session,
            merchant_id=principal.merchant_id,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if replay_after_race is not None:
            return replay_after_race
        raise HTTPException(status_code=409, detail="payment_request_conflict") from None

    try:
        provider_result = await initiate_stk_push(
            environment=integration.environment,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            passkey=passkey,
            shortcode=integration.shortcode or "",
            party_b_shortcode=integration.party_b_shortcode or integration.shortcode or "",
            product_type=integration.product_type or "paybill",
            phone_number=body.phone_number,
            amount_kes=body.amount_kes,
            callback_url=integration.stk_callback_url or "",
            account_reference="NP" + payment.id.hex[:10],
            transaction_description=body.description,
            timeout_seconds=settings.daraja_timeout_seconds,
        )
    except DarajaStkRejected as exc:
        now = datetime.now(UTC)
        payment.status = "failed"
        payment.provider_result_code = exc.safe_code
        payment.provider_result_description = "Daraja rejected the STK request"
        payment.failed_at = now
        payment.completed_at = now
        attempt.status = "rejected"
        attempt.safe_error_code = exc.safe_code
        attempt.safe_error_message = "Daraja rejected the STK request"
        provider_request.outcome = "rejected"
        provider_request.response_metadata = {"outcome": "rejected", "code": exc.safe_code}
        provider_request.completed_at = now
    except DarajaStkUncertain:
        now = datetime.now(UTC)
        payment.status = "unknown"
        payment.provider_result_description = "Provider outcome is unknown; reconcile before retrying"
        attempt.status = "unknown"
        attempt.safe_error_code = "provider_outcome_unknown"
        attempt.safe_error_message = "Provider outcome is unknown; reconcile before retrying"
        provider_request.outcome = "unknown"
        provider_request.response_metadata = {"outcome": "unknown"}
        provider_request.completed_at = now
    else:
        now = datetime.now(UTC)
        payment.provider_checkout_request_id = provider_result["checkout_request_id"]
        payment.provider_merchant_request_id = provider_result["merchant_request_id"]
        payment.provider_result_code = provider_result["response_code"]
        payment.provider_result_description = "STK request accepted; awaiting provider result"
        payment.initiated_at = now
        attempt.status = "accepted"
        provider_request.provider_request_id = provider_result["merchant_request_id"]
        provider_request.http_status = 200
        provider_request.outcome = "accepted"
        provider_request.response_metadata = {
            "response_code": provider_result["response_code"],
            "checkout_request_id": provider_result["checkout_request_id"],
            "merchant_request_id": provider_result["merchant_request_id"],
        }
        provider_request.completed_at = now
    await session.commit()
    return _to_response(payment)


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Inspect a merchant payment")
async def get_payment(
    payment_id: UUID,
    principal: MachinePrincipal = Depends(require_scopes("payments:read")),
    session: AsyncSession = Depends(get_session),
) -> PaymentResponse:
    """Read a payment only when it belongs to the authenticated merchant."""
    result = await session.exec(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.merchant_id == principal.merchant_id,
            Payment.deleted_at.is_(None),
        )
    )
    payment = result.first()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment_not_found")
    return _to_response(payment)
