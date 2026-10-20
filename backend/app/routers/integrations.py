"""Merchant-scoped Daraja integration onboarding and listing."""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import MerchantPrincipal, require_scope
from app.config import get_settings
from app.crypto import decrypt_secret, encrypt_secret
from app.daraja.c2b import C2BRegistrationRejected, C2BRegistrationUnknown, register_c2b_urls
from app.daraja.client import DarajaUnavailable, InvalidDarajaCredentials, request_access_token
from app.db import get_session
from app.models import DarajaIntegration
from app.schemas import IntegrationCreate, IntegrationList, IntegrationSummary

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.post("", response_model=IntegrationSummary, status_code=status.HTTP_201_CREATED)
async def create_integration(
    payload: IntegrationCreate,
    principal: MerchantPrincipal = Depends(require_scope("integrations:write")),
    session: AsyncSession = Depends(get_session),
) -> DarajaIntegration:
    """Validate OAuth credentials and save encrypted merchant configuration."""
    existing = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.shortcode == payload.shortcode,
            DarajaIntegration.environment == payload.environment,
        )
    )
    if existing.first() is not None:
        raise HTTPException(status_code=409, detail={"code": "integration_exists", "message": "An integration for this shortcode and environment already exists"})

    try:
        await request_access_token(
            payload.environment,
            payload.consumer_key.get_secret_value(),
            payload.consumer_secret.get_secret_value(),
        )
    except InvalidDarajaCredentials as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_daraja_credentials", "message": "Daraja rejected the consumer credentials"}) from exc
    except DarajaUnavailable as exc:
        raise HTTPException(status_code=502, detail={"code": "daraja_unavailable", "message": "Could not validate credentials with Daraja; try again later"}) from exc

    public_id = secrets.token_urlsafe(24)
    base_url = get_settings().public_base_url.rstrip("/")
    integration = DarajaIntegration(
        integration_id=public_id,
        merchant_id=principal.merchant_id,
        environment=payload.environment,
        shortcode=payload.shortcode,
        party_b_shortcode=payload.party_b_shortcode or payload.shortcode,
        product_type=payload.product_type,
        consumer_key_ciphertext=encrypt_secret(payload.consumer_key.get_secret_value()),
        consumer_secret_ciphertext=encrypt_secret(payload.consumer_secret.get_secret_value()),
        passkey_ciphertext=encrypt_secret(payload.passkey.get_secret_value()),
        credential_status="oauth_validated",
        c2b_enabled=False,
        c2b_registration_status="not_requested",
        stk_callback_url=f"{base_url}/cb/stk/{public_id}",
        c2b_validation_url=f"{base_url}/cb/c2b/validation/{public_id}",
        c2b_confirmation_url=f"{base_url}/cb/c2b/confirmation/{public_id}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(integration)
    try:
        await session.commit()
        await session.refresh(integration)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail={"code": "integration_conflict", "message": "An integration with these details already exists"}) from exc
    return integration


@router.get("", response_model=IntegrationList)
async def list_integrations(
    principal: MerchantPrincipal = Depends(require_scope("integrations:read")),
    session: AsyncSession = Depends(get_session),
) -> IntegrationList:
    result = await session.exec(
        select(DarajaIntegration)
        .where(DarajaIntegration.merchant_id == principal.merchant_id)
        .order_by(DarajaIntegration.created_at.desc())
    )
    return IntegrationList(items=list(result.all()))


@router.get("/{integration_id}", response_model=IntegrationSummary)
async def get_integration(
    integration_id: str,
    principal: MerchantPrincipal = Depends(require_scope("integrations:read")),
    session: AsyncSession = Depends(get_session),
) -> DarajaIntegration:
    result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
        )
    )
    integration = result.first()
    if integration is None:
        raise HTTPException(status_code=404, detail={"code": "integration_not_found", "message": "Integration not found"})
    return integration


@router.post("/{integration_id}/c2b/enable", response_model=IntegrationSummary)
async def enable_c2b(
    integration_id: str,
    principal: MerchantPrincipal = Depends(require_scope("integrations:write")),
    session: AsyncSession = Depends(get_session),
) -> DarajaIntegration:
    """Explicitly opt a merchant into C2B URL registration."""
    result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
        )
    )
    integration = result.first()
    if integration is None:
        raise HTTPException(status_code=404, detail={"code": "integration_not_found", "message": "Integration not found"})
    if integration.c2b_registration_status == "registered":
        return integration
    if integration.c2b_registration_status in {"registering", "unknown"}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "registration_outcome_unknown",
                "message": "Check Daraja URL management before retrying registration; the request may already have succeeded",
            },
        )
    if integration.credential_status != "oauth_validated":
        raise HTTPException(status_code=409, detail={"code": "integration_not_ready", "message": "Validate Daraja credentials before enabling C2B"})

    integration.c2b_enabled = True
    integration.c2b_registration_status = "registering"
    integration.registration_error = None
    integration.updated_at = datetime.now(timezone.utc)
    session.add(integration)
    await session.commit()

    try:
        await register_c2b_urls(
            environment=integration.environment,
            consumer_key=decrypt_secret(integration.consumer_key_ciphertext),
            consumer_secret=decrypt_secret(integration.consumer_secret_ciphertext),
            shortcode=integration.shortcode,
            validation_url=integration.c2b_validation_url,
            confirmation_url=integration.c2b_confirmation_url,
        )
    except C2BRegistrationUnknown:
        integration.c2b_registration_status = "unknown"
        integration.registration_error = "Registration outcome unknown; verify Daraja URL management before retrying"
    except C2BRegistrationRejected as exc:
        integration.c2b_registration_status = "failed"
        integration.registration_error = "Daraja rejected URL registration"
        integration.updated_at = datetime.now(timezone.utc)
        session.add(integration)
        await session.commit()
        raise HTTPException(status_code=422, detail={"code": "c2b_registration_rejected", "message": "Daraja rejected C2B URL registration"}) from exc
    except InvalidDarajaCredentials as exc:
        integration.c2b_registration_status = "failed"
        integration.registration_error = "Daraja rejected the consumer credentials"
        integration.updated_at = datetime.now(timezone.utc)
        session.add(integration)
        await session.commit()
        raise HTTPException(status_code=422, detail={"code": "invalid_daraja_credentials", "message": "Daraja rejected the consumer credentials"}) from exc
    except DarajaUnavailable as exc:
        integration.c2b_registration_status = "failed"
        integration.registration_error = "Daraja OAuth was unavailable before registration was submitted"
        integration.updated_at = datetime.now(timezone.utc)
        session.add(integration)
        await session.commit()
        raise HTTPException(status_code=502, detail={"code": "daraja_unavailable", "message": "Could not reach Daraja before registration was submitted"}) from exc
    else:
        integration.c2b_registration_status = "registered"
        integration.registration_error = None

    integration.updated_at = datetime.now(timezone.utc)
    session.add(integration)
    await session.commit()
    await session.refresh(integration)
    return integration
