"""Application-owned M-Pesa integration, STK, status, and callback routes."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from loguru import logger
from pydantic import SecretStr, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.attempts import PaymentAttempt
from app.models.events import EventOutbox
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient, Merchant
from app.models.operations import AuditLog, ProviderRequest
from app.models.payments import IdempotencyRecord, Payment, ProviderCallback
from app.mpesa_core import DarajaCredentials, IntegrationContext
from app.mpesa_core.credentials import decrypt_credentials, encrypt_credentials
from app.mpesa_core.callbacks import callback_fingerprint, parse_c2b_callback, parse_stk_callback
from app.mpesa_core.errors import (
    AmbiguousOutcome,
    MalformedProviderResponse,
    MpesaCoreError,
    ProviderRejected,
    TransportFailure,
)
from app.mpesa_core.schemas import C2BRegistrationRequest, STKPushRequest
from app.mpesa_core.validation import normalize_ke_phone
from app.payments.schemas import (
    IntegrationCreate,
    IntegrationView,
    PaymentView,
    STKInitiation,
    TokenRequest,
)
from app.payments.security import (
    Principal,
    issue_access_token,
    require_scopes,
    verify_client_secret,
)

router = APIRouter()
payments_read = require_scopes("payments:read")
payments_write = require_scopes("payments:write")
integrations_write = require_scopes("integrations:write")


def _core(request: Request):
    core = getattr(request.app.state, "mpesa_core", None)
    if core is None:
        raise HTTPException(status_code=503, detail="mpesa_core_unavailable")
    return core


def _integration_view(row: DarajaIntegration) -> IntegrationView:
    return IntegrationView(
        id=row.id,
        integration_id=row.integration_id,
        environment=row.environment,
        shortcode=row.shortcode or "",
        product_type=row.product_type,
        status=row.status,
        credential_status=row.credential_status,
        enabled_capabilities=list(row.enabled_capabilities),
        stk_callback_url=row.stk_callback_url or "",
        c2b_validation_url=row.c2b_validation_url or "",
        c2b_confirmation_url=row.c2b_confirmation_url or "",
        c2b_enabled=row.c2b_enabled,
        c2b_registration_status=row.c2b_registration_status,
    )


def _payment_view(row: Payment) -> PaymentView:
    return PaymentView(
        id=row.id,
        merchant_reference=row.merchant_reference,
        amount_minor=row.amount_minor,
        currency=row.currency,
        status=row.status,
        provider_checkout_request_id=row.provider_checkout_request_id,
        provider_merchant_request_id=row.provider_merchant_request_id,
        provider_receipt=row.provider_receipt,
        provider_result_code=row.provider_result_code,
        created_at=row.created_at.isoformat(),
    )


def _context(row: DarajaIntegration) -> IntegrationContext:
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


def _callback_metadata(callback: Any) -> dict[str, Any]:
    metadata = callback.callback_metadata or {}
    items = metadata.get("Item", []) if isinstance(metadata, dict) else []
    selected: dict[str, Any] = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("Name") in {
                "Amount", "MpesaReceiptNumber", "PhoneNumber", "TransactionDate",
            }:
                selected[str(item["Name"])] = item.get("Value")
    return selected


def _event(session: AsyncSession, payment: Payment, event_type: str) -> None:
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


async def _apply_stk_callback(
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
    callback_phone = metadata.get("PhoneNumber")
    if callback_phone is not None:
        try:
            if normalize_ke_phone(str(callback_phone)) != payment.phone_number:
                callback_row.processing_status = "rejected"
                callback_row.processing_error = "phone_mismatch"
                return False
        except MpesaCoreError:
            callback_row.processing_status = "rejected"
            callback_row.processing_error = "invalid_callback_phone"
            return False
        except ValueError:
            callback_row.processing_status = "rejected"
            callback_row.processing_error = "invalid_callback_phone"
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
        _event(session, payment, "payment.succeeded")
    else:
        payment.status = "failed"
        payment.failed_at = now
        payment.completed_at = now
        _event(session, payment, "payment.failed")
    callback_row.payment_id = payment.id
    callback_row.merchant_id = payment.merchant_id
    callback_row.processing_status = "processed"
    callback_row.processing_error = None
    callback_row.processed_at = now
    return True


@router.post("/api/v1/oauth/token", tags=["authentication"])
async def token_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Exchange a provisioned M2M client credential for a short-lived bearer token."""
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    try:
        if "application/json" in content_type:
            values = json.loads(body or b"{}")
        else:
            from urllib.parse import parse_qs
            parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
            values = {key: value[-1] for key, value in parsed.items()}
        request_data = TokenRequest.model_validate(values)
    except (ValueError, UnicodeDecodeError, ValidationError):
        raise HTTPException(status_code=400, detail="invalid_token_request") from None
    client = await session.scalar(select(M2MClient).where(M2MClient.client_id == request_data.client_id))
    if client is None or client.status != "active" or client.revoked_at is not None:
        raise HTTPException(status_code=401, detail="invalid_client", headers={"WWW-Authenticate": "Bearer"})
    if not verify_client_secret(request_data.client_secret.get_secret_value(), client.secret_hash):
        raise HTTPException(status_code=401, detail="invalid_client", headers={"WWW-Authenticate": "Bearer"})
    now = datetime.now(UTC)
    if client.expires_at is not None and client.expires_at <= now:
        raise HTTPException(status_code=401, detail="client_expired")
    merchant = await session.get(Merchant, client.merchant_id)
    if merchant is None or merchant.status != "active" or merchant.deleted_at is not None:
        raise HTTPException(status_code=403, detail="merchant_inactive")
    client.last_used_at = now
    granted_scopes = list(client.scopes)
    if request_data.scope:
        requested_scopes = set(request_data.scope.split())
        if not requested_scopes.issubset(set(client.scopes)):
            raise HTTPException(status_code=400, detail="invalid_scope")
        granted_scopes = sorted(requested_scopes)
    token_value = issue_access_token(client, merchant, scopes=granted_scopes)
    await session.commit()
    return {"access_token": token_value, "token_type": "Bearer", "expires_in": 900, "scope": " ".join(granted_scopes)}


@router.post("/api/v1/integrations", response_model=IntegrationView, status_code=201, tags=["integrations"])
async def create_integration(
    payload: IntegrationCreate,
    request: Request,
    principal: Principal = Depends(integrations_write),
    session: AsyncSession = Depends(get_session),
) -> IntegrationView:
    """Validate Daraja OAuth, encrypt credentials, and persist an active merchant integration."""
    settings = get_settings()
    if not settings.mpesa_public_base_url:
        raise HTTPException(status_code=503, detail="mpesa_public_base_url_not_configured")
    base_url = settings.mpesa_public_base_url.rstrip("/")
    integration = DarajaIntegration(
        merchant_id=principal.merchant_id,
        environment=payload.environment,
        status="pending",
        credential_status="pending",
        shortcode=payload.shortcode,
        party_b_shortcode=payload.party_b_shortcode,
        product_type=payload.product_type,
        enabled_capabilities=["stk_push"],
    )
    try:
        integration.credentials_ciphertext = encrypt_credentials(json.dumps({
            "consumer_key": payload.consumer_key.get_secret_value(),
            "consumer_secret": payload.consumer_secret.get_secret_value(),
            "passkey": payload.passkey.get_secret_value(),
        }, separators=(",", ":")).encode())
    except HTTPException:
        raise
    integration.stk_callback_url = f"{base_url}/callbacks/mpesa/stk/{integration.integration_id}"
    integration.c2b_validation_url = f"{base_url}/callbacks/mpesa/c2b/{integration.integration_id}/validation"
    integration.c2b_confirmation_url = f"{base_url}/callbacks/mpesa/c2b/{integration.integration_id}/confirmation"
    context = IntegrationContext(
        integration_id=integration.integration_id,
        environment=payload.environment,
        shortcode=payload.shortcode,
        product_type=payload.product_type,
        party_b_shortcode=payload.party_b_shortcode,
        enabled_capabilities=frozenset({"stk_push"}),
        credentials=DarajaCredentials(
            consumer_key=payload.consumer_key,
            consumer_secret=payload.consumer_secret,
            passkey=payload.passkey,
        ),
    )
    try:
        await _core(request).validate_credentials(context)
    except MpesaCoreError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
    integration.status = "active"
    integration.credential_status = "validated"
    integration.credentials_validated_at = datetime.now(UTC)
    session.add(integration)
    session.add(AuditLog(
        merchant_id=principal.merchant_id,
        actor_type="m2m_client",
        actor_id=principal.client_id,
        action="integration.created",
        resource_type="daraja_integration",
        resource_id=integration.id,
        metadata_json={"environment": payload.environment, "shortcode": payload.shortcode, "product_type": payload.product_type},
    ))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="integration_already_exists_for_environment") from None
    await session.refresh(integration)
    logger.info("mpesa_integration_created merchant_id={} integration_id={} environment={}", principal.merchant_id, integration.integration_id, integration.environment)
    return _integration_view(integration)


@router.get("/api/v1/integrations", response_model=list[IntegrationView], tags=["integrations"])
async def list_integrations(
    principal: Principal = Depends(integrations_write),
    session: AsyncSession = Depends(get_session),
) -> list[IntegrationView]:
    """List only the authenticated merchant's integrations; never return credentials."""
    rows = (await session.exec(select(DarajaIntegration).where(
        DarajaIntegration.merchant_id == principal.merchant_id,
        DarajaIntegration.deleted_at.is_(None),
    ).order_by(DarajaIntegration.created_at.desc()))).all()
    return [_integration_view(row) for row in rows]


@router.post("/api/v1/integrations/{integration_id}/c2b/register", tags=["integrations"])
async def register_c2b(
    integration_id: str,
    request: Request,
    principal: Principal = Depends(integrations_write),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Explicitly opt in to C2B URL registration; ambiguous outcomes are never retried here."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.merchant_id == principal.merchant_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None:
        raise HTTPException(status_code=404, detail="integration_not_found")
    if integration.status != "active":
        raise HTTPException(status_code=409, detail="integration_not_active")
    if integration.environment == "production":
        raise HTTPException(status_code=409, detail="c2b_production_registration_gated_pending_provider_verification")
    if integration.c2b_registration_status in {"unknown", "started"}:
        raise HTTPException(status_code=409, detail="c2b_registration_outcome_requires_reconciliation")
    if "c2b_registration" not in integration.enabled_capabilities:
        integration.enabled_capabilities = list(set(integration.enabled_capabilities) | {"c2b_registration"})
    integration.c2b_enabled = True
    context = _context(integration)
    integration.c2b_registration_status = "started"
    integration.registration_error = None
    await session.commit()
    try:
        result = await _core(request).register_c2b_urls(
            context,
            C2BRegistrationRequest(
                validation_url=integration.c2b_validation_url or "",
                confirmation_url=integration.c2b_confirmation_url or "",
                response_type="Completed",
            ),
        )
    except (AmbiguousOutcome, MalformedProviderResponse) as exc:
        integration.c2b_registration_status = "unknown"
        integration.registration_error = exc.code
        await session.commit()
        raise HTTPException(status_code=202, detail="c2b_registration_outcome_unknown_do_not_retry") from None
    except MpesaCoreError as exc:
        integration.c2b_registration_status = "failed"
        integration.c2b_enabled = False
        integration.registration_error = exc.code
        await session.commit()
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
    integration.c2b_registration_status = "registered"
    integration.c2b_registered_at = datetime.now(UTC)
    await session.commit()
    return {"integration_id": integration.integration_id, "registration_status": integration.c2b_registration_status, "provider_outcome": result.outcome.value}


@router.post("/api/v1/payments/stk", response_model=PaymentView, status_code=202, tags=["payments"])
async def initiate_stk(
    payload: STKInitiation,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(payments_write),
    session: AsyncSession = Depends(get_session),
) -> PaymentView:
    """Create a durable payment attempt before sending STK; acceptance never means paid."""
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
    context = _context(integration)
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
        return _payment_view(payment)

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
    session.add_all([attempt, provider_request, idempotency])
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
                return _payment_view(payment)
        raise HTTPException(status_code=409, detail="payment_request_conflict") from None

    try:
        result = await _core(request).stk_push(
            context,
            STKPushRequest(
                phone_number=phone,
                amount_minor=payload.amount_minor,
                account_reference=payment.id.hex[:12],
                description=payload.description[:13],
                callback_url=integration.stk_callback_url or "",
            ),
        )
        payment.provider_checkout_request_id = result.response.get("CheckoutRequestID")
        payment.provider_merchant_request_id = result.response.get("MerchantRequestID")
        payment.initiated_at = datetime.now(UTC)
        payment.status = "pending"
        attempt.status = "accepted"
        provider_request.outcome = result.outcome.value
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
                await _apply_stk_callback(session, integration, callback_row)
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
            _event(session, payment, "payment.failed")
        await session.commit()
        if isinstance(exc, (AmbiguousOutcome, MalformedProviderResponse)):
            return _payment_view(payment)
        if isinstance(exc, TransportFailure):
            raise HTTPException(status_code=502, detail={"code": exc.code, "message": "Provider connection failed before request transmission"}) from None
        if isinstance(exc, ProviderRejected):
            raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
        raise HTTPException(status_code=502, detail={"code": exc.code, "message": exc.safe_message}) from None
    return _payment_view(payment)


@router.get("/api/v1/payments/{payment_id}", response_model=PaymentView, tags=["payments"])
async def get_payment(
    payment_id: UUID,
    principal: Principal = Depends(payments_read),
    session: AsyncSession = Depends(get_session),
) -> PaymentView:
    """Read payment status within the authenticated merchant's scope."""
    payment = await session.scalar(select(Payment).where(
        Payment.id == payment_id,
        Payment.merchant_id == principal.merchant_id,
        Payment.deleted_at.is_(None),
    ))
    if payment is None:
        raise HTTPException(status_code=404, detail="payment_not_found")
    return _payment_view(payment)


@router.post("/callbacks/mpesa/stk/{integration_id}", include_in_schema=False)
async def stk_callback(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Receive untrusted Daraja STK callbacks and persist evidence before acknowledging."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None or integration.status != "active":
        raise HTTPException(status_code=404, detail="integration_not_found")
    try:
        callback = parse_stk_callback(payload)
    except MpesaCoreError as exc:
        raise HTTPException(status_code=400, detail=exc.safe_message) from None
    fingerprint = callback_fingerprint(payload)
    metadata = _callback_metadata(callback)
    safe_payload = {
        "checkout_request_id": callback.checkout_request_id,
        "merchant_request_id": callback.merchant_request_id,
        "result_code": callback.result_code,
        "result_description": callback.result_description[:250],
        "metadata": metadata,
    }
    row = ProviderCallback(
        integration_id=integration.id,
        provider_event_id=fingerprint,
        merchant_id=integration.merchant_id,
        callback_type="stk",
        dedupe_fingerprint=fingerprint,
        payload=safe_payload,
        processing_status="received",
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    await _apply_stk_callback(session, integration, row)
    await session.commit()
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/callbacks/mpesa/c2b/{integration_id}/validation", include_in_schema=False)
async def c2b_validation(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Validate an explicitly enabled C2B callback; disabled integrations are rejected."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None or integration.status != "active" or not integration.c2b_enabled:
        return {"ResultCode": 1, "ResultDesc": "Rejected"}
    try:
        callback = parse_c2b_callback(payload)
        amount = Decimal(callback.trans_amount)
        if amount <= 0 or amount * 100 != int(amount * 100):
            raise ValueError
        if callback.business_short_code != integration.shortcode:
            raise ValueError
    except (MpesaCoreError, InvalidOperation, ValueError):
        return {"ResultCode": 1, "ResultDesc": "Rejected"}
    return {"ResultCode": "0", "ResultDesc": "Accepted"}


@router.post("/callbacks/mpesa/c2b/{integration_id}/confirmation", include_in_schema=False)
async def c2b_confirmation(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Persist and deduplicate C2B confirmation before acknowledging the provider."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None or integration.status != "active" or not integration.c2b_enabled:
        return {"ResultCode": "C2B0001", "ResultDesc": "Rejected"}
    try:
        callback = parse_c2b_callback(payload)
        amount = Decimal(callback.trans_amount)
        if amount <= 0 or amount * 100 != int(amount * 100) or callback.business_short_code != integration.shortcode:
            raise ValueError
        amount_minor = int(amount * 100)
    except (MpesaCoreError, InvalidOperation, ValueError):
        return {"ResultCode": "C2B0001", "ResultDesc": "Rejected"}
    fingerprint = callback_fingerprint(payload)
    existing = await session.scalar(select(Payment).where(
        Payment.integration_id == integration.id,
        Payment.provider_receipt == callback.trans_id,
    ))
    if existing is not None:
        return {"ResultCode": "0", "ResultDesc": "Accepted"}
    payment = Payment(
        merchant_id=integration.merchant_id,
        integration_id=integration.id,
        merchant_reference=f"c2b:{callback.trans_id}"[:120],
        amount_minor=amount_minor,
        currency="KES",
        phone_number=callback.msisdn,
        payment_source="c2b",
        direction="inbound",
        description="C2B confirmation",
        status="succeeded",
        provider_transaction_id=callback.trans_id,
        provider_receipt=callback.trans_id,
        provider_result_code="0",
        provider_result_description="C2B confirmation",
        completed_at=datetime.now(UTC),
        succeeded_at=datetime.now(UTC),
    )
    row = ProviderCallback(
        integration_id=integration.id,
        provider_event_id=fingerprint,
        merchant_id=integration.merchant_id,
        callback_type="c2b_confirmation",
        dedupe_fingerprint=fingerprint,
        provider_transaction_id=callback.trans_id,
        payload={
            "trans_id": callback.trans_id,
            "trans_amount": str(amount),
            "business_short_code": callback.business_short_code,
            "bill_ref_number": callback.bill_ref_number,
        },
        processing_status="processed",
        processed_at=datetime.now(UTC),
    )
    session.add_all([payment, row])
    try:
        await session.flush()
        row.payment_id = payment.id
        _event(session, payment, "payment.succeeded")
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return {"ResultCode": "0", "ResultDesc": "Accepted"}
    return {"ResultCode": "0", "ResultDesc": "Accepted"}
