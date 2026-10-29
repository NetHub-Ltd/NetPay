"""Application-owned M-Pesa integration, STK, status, and callback routes."""
from __future__ import annotations

import json
import hashlib
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
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient, Merchant
from app.models.operations import AuditLog
from app.models.payments import Payment, ProviderCallback
from app.mpesa_core import DarajaCredentials, IntegrationContext
from app.mpesa_core.credentials import encrypt_credentials
from app.mpesa_core.callbacks import callback_fingerprint, parse_c2b_callback, parse_stk_callback
from app.mpesa_core.errors import (
    AmbiguousOutcome,
    CredentialStorageError,
    MalformedProviderResponse,
    MpesaCoreError,
)
from app.mpesa_core.schemas import C2BRegistrationRequest
from app.mpesa_core.validation import normalize_ke_phone, validate_callback_url
from app.payments.service import PaymentApplicationService
from app.payments.schemas import (
    IntegrationCreate,
    IntegrationCredentialRotation,
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
integrations_read = require_scopes("integrations:read")
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
        c2b_registered_at=row.c2b_registered_at,
        registration_error=row.registration_error,
        credentials_validated_at=row.credentials_validated_at,
        credential_version=row.credential_version,
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
    except CredentialStorageError as exc:
        raise HTTPException(status_code=503, detail=exc.code) from None
    integration.stk_callback_url = f"{base_url}/callbacks/mpesa/stk/{integration.integration_id}"
    integration.c2b_validation_url = f"{base_url}/callbacks/mpesa/c2b/{integration.integration_id}/validation"
    integration.c2b_confirmation_url = f"{base_url}/callbacks/mpesa/c2b/{integration.integration_id}/confirmation"
    try:
        validate_callback_url(integration.stk_callback_url, production=payload.environment == "production")
    except MpesaCoreError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
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


@router.put("/api/v1/integrations/{integration_id}/credentials", response_model=IntegrationView, tags=["integrations"])
async def rotate_integration_credentials(
    integration_id: str,
    payload: IntegrationCredentialRotation,
    request: Request,
    principal: Principal = Depends(integrations_write),
    session: AsyncSession = Depends(get_session),
) -> IntegrationView:
    """Validate replacement credentials before atomically replacing encrypted material."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.merchant_id == principal.merchant_id,
        DarajaIntegration.deleted_at.is_(None),
    ).with_for_update())
    if integration is None:
        raise HTTPException(status_code=404, detail="integration_not_found")
    next_version = integration.credential_version + 1
    new_credentials = DarajaCredentials(
        consumer_key=payload.consumer_key,
        consumer_secret=payload.consumer_secret,
        passkey=payload.passkey,
        credential_version=next_version,
    )
    try:
        ciphertext = encrypt_credentials(json.dumps({
            "consumer_key": payload.consumer_key.get_secret_value(),
            "consumer_secret": payload.consumer_secret.get_secret_value(),
            "passkey": payload.passkey.get_secret_value(),
        }, separators=(",", ":")).encode())
    except CredentialStorageError as exc:
        raise HTTPException(status_code=503, detail=exc.code) from None
    context = IntegrationContext(
        integration_id=integration.integration_id,
        environment=integration.environment,
        shortcode=integration.shortcode or "",
        product_type=integration.product_type,
        party_b_shortcode=integration.party_b_shortcode,
        enabled_capabilities=frozenset(integration.enabled_capabilities),
        credentials=new_credentials,
    )
    try:
        await _core(request).validate_credentials(context)
    except MpesaCoreError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.safe_message}) from None
    integration.credentials_ciphertext = ciphertext
    integration.credential_version = next_version
    integration.credential_status = "validated"
    integration.credentials_validated_at = datetime.now(UTC)
    session.add(AuditLog(
        merchant_id=principal.merchant_id,
        actor_type="m2m_client",
        actor_id=principal.client_id,
        action="integration.credentials_rotated",
        resource_type="daraja_integration",
        resource_id=integration.id,
        metadata_json={"credential_version": next_version},
    ))
    await session.commit()
    await session.refresh(integration)
    logger.info("mpesa_credentials_rotated merchant_id={} integration_id={} credential_version={}", principal.merchant_id, integration.integration_id, next_version)
    return _integration_view(integration)


@router.get("/api/v1/integrations", response_model=list[IntegrationView], tags=["integrations"])
async def list_integrations(
    principal: Principal = Depends(integrations_read),
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
    ).with_for_update())
    if integration is None:
        raise HTTPException(status_code=404, detail="integration_not_found")
    if integration.status != "active":
        raise HTTPException(status_code=409, detail="integration_not_active")
    if integration.environment == "production":
        raise HTTPException(status_code=409, detail="c2b_production_registration_gated_pending_provider_verification")
    if integration.c2b_registration_status == "registered":
        return {"integration_id": integration.integration_id, "registration_status": "registered", "provider_outcome": "already_registered"}
    if integration.c2b_registration_status in {"unknown", "started"}:
        raise HTTPException(status_code=409, detail="c2b_registration_outcome_requires_reconciliation")
    if "c2b_registration" not in integration.enabled_capabilities:
        integration.enabled_capabilities = list(set(integration.enabled_capabilities) | {"c2b_registration"})
    integration.c2b_enabled = True
    context = PaymentApplicationService.context_for_integration(integration)
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
    """Create a durable payment attempt; provider acceptance never means paid."""
    service = PaymentApplicationService(session, _core(request), principal)
    payment = await service.initiate_stk(payload, idempotency_key)
    return _payment_view(payment)


@router.get("/api/v1/payments/{payment_id}", response_model=PaymentView, tags=["payments"])
async def get_payment(
    payment_id: UUID,
    principal: Principal = Depends(payments_read),
    session: AsyncSession = Depends(get_session),
) -> PaymentView:
    """Return the canonical status of a payment owned by the authenticated merchant."""
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
) -> dict[str, Any]:
    """Persist, correlate and deduplicate STK callbacks before acknowledging Daraja."""
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
    existing = await session.scalar(select(ProviderCallback).where(
        ProviderCallback.integration_id == integration.id,
        ProviderCallback.dedupe_fingerprint == fingerprint,
    ))
    if existing is not None:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    metadata = _callback_metadata(callback)
    callback_phone = metadata.pop("PhoneNumber", None)
    if callback_phone is not None:
        try:
            metadata["PhoneNumberLast4"] = normalize_ke_phone(str(callback_phone))[-4:]
        except MpesaCoreError:
            metadata["PhoneNumberLast4"] = "invalid"
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
    await PaymentApplicationService.apply_stk_callback(session, integration, row)
    await session.commit()
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/callbacks/mpesa/c2b/{integration_id}/validation", include_in_schema=False)
async def c2b_validation(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Persist and deduplicate the validation decision without retaining raw callback PII."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None or integration.status != "active" or not integration.c2b_enabled:
        return {"ResultCode": 1, "ResultDesc": "Rejected"}
    integration_pk = integration.id

    fingerprint = hashlib.sha256(f"c2b_validation:{callback_fingerprint(payload)}".encode()).hexdigest()
    safe_payload: dict[str, Any] = {"field_names": sorted(payload.keys())}
    processing_status = "rejected"
    processing_error = "invalid_c2b_validation"
    callback = None
    try:
        callback = parse_c2b_callback(payload)
        amount = Decimal(callback.trans_amount)
        if (
            amount <= 0
            or amount * 100 != int(amount * 100)
            or callback.business_short_code != integration.shortcode
            or not 1 <= len(callback.trans_id) <= 64
        ):
            raise ValueError("c2b_validation_mismatch")
        phone_last4 = None
        if callback.msisdn:
            phone_last4 = normalize_ke_phone(callback.msisdn)[-4:]
        safe_payload = {
            "trans_id": callback.trans_id,
            "trans_amount": str(amount),
            "business_short_code": callback.business_short_code,
            "bill_ref_number": callback.bill_ref_number,
            "msisdn_last4": phone_last4,
        }
        processing_status = "processed"
        processing_error = ""
    except (MpesaCoreError, InvalidOperation, ValueError) as exc:
        processing_error = exc.code if isinstance(exc, MpesaCoreError) else "c2b_validation_mismatch"

    now = datetime.now(UTC)
    row = ProviderCallback(
        integration_id=integration.id,
        provider_event_id=fingerprint,
        merchant_id=integration.merchant_id,
        callback_type="c2b_validation",
        dedupe_fingerprint=fingerprint,
        provider_transaction_id=callback.trans_id if callback is not None else None,
        payload=safe_payload,
        processing_status=processing_status,
        processing_error=processing_error or None,
        processed_at=now,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await session.scalar(select(ProviderCallback).where(
            ProviderCallback.integration_id == integration_pk,
            ProviderCallback.dedupe_fingerprint == fingerprint,
        ))
        accepted = existing is not None and existing.processing_status == "processed"
        return {"ResultCode": 0 if accepted else 1, "ResultDesc": "Accepted" if accepted else "Rejected"}
    accepted = processing_status == "processed"
    return {"ResultCode": 0 if accepted else 1, "ResultDesc": "Accepted" if accepted else "Rejected"}


@router.post("/callbacks/mpesa/c2b/{integration_id}/confirmation", include_in_schema=False)
async def c2b_confirmation(
    integration_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Persist and deduplicate C2B confirmation before acknowledging the provider."""
    integration = await session.scalar(select(DarajaIntegration).where(
        DarajaIntegration.integration_id == integration_id,
        DarajaIntegration.deleted_at.is_(None),
    ))
    if integration is None or integration.status != "active" or not integration.c2b_enabled:
        return {"ResultCode": 1, "ResultDesc": "Rejected"}
    try:
        callback = parse_c2b_callback(payload)
        amount = Decimal(callback.trans_amount)
        if (
            amount <= 0
            or amount * 100 != int(amount * 100)
            or callback.business_short_code != integration.shortcode
            or not 1 <= len(callback.trans_id) <= 64
        ):
            raise ValueError
        amount_minor = int(amount * 100)
    except (MpesaCoreError, InvalidOperation, ValueError):
        return {"ResultCode": 1, "ResultDesc": "Rejected"}
    fingerprint = hashlib.sha256(f"c2b_confirmation:{callback_fingerprint(payload)}".encode()).hexdigest()
    existing = await session.scalar(select(Payment).where(
        Payment.integration_id == integration.id,
        Payment.provider_receipt == callback.trans_id,
    ))
    if existing is not None:
        if existing.amount_minor != amount_minor or existing.merchant_id != integration.merchant_id:
            return {"ResultCode": 1, "ResultDesc": "Rejected"}
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
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
        PaymentApplicationService.add_event(session, payment, "payment.succeeded")
        session.add(AuditLog(
            merchant_id=integration.merchant_id,
            actor_type="provider_callback",
            action="payment.c2b_confirmed",
            resource_type="payment",
            resource_id=payment.id,
            metadata_json={"callback_id": str(row.id), "provider_transaction_id": callback.trans_id, "amount_minor": amount_minor},
        ))
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
