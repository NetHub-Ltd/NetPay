"""Merchant-scoped Daraja integration onboarding and inspection endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.credentials import CredentialEncryptionError, encrypt_credential
from app.core.database import get_session
from app.core.machine_auth import MachinePrincipal, require_scopes
from app.models.integrations import DarajaIntegration
from app.models.operations import AuditLog
from app.providers.daraja import DarajaCredentialsRejected, DarajaUnavailable, validate_daraja_credentials

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


class IntegrationCreateRequest(BaseModel):
    """Provider credentials and merchant-owned shortcode configuration."""

    environment: Literal["sandbox", "production"] = "sandbox"
    shortcode: str = Field(min_length=1, max_length=32)
    party_b_shortcode: str | None = Field(default=None, min_length=1, max_length=32)
    product_type: Literal["paybill", "till"]
    consumer_key: SecretStr = Field(min_length=1, max_length=256)
    consumer_secret: SecretStr = Field(min_length=1, max_length=256)
    passkey: SecretStr = Field(min_length=1, max_length=256)

    @field_validator("shortcode", "party_b_shortcode")
    @classmethod
    def validate_shortcode_digits(cls, value: str | None) -> str | None:
        """Accept only numeric Daraja shortcodes."""
        if value is not None and not value.isdigit():
            raise ValueError("Shortcodes must contain digits only")
        return value


class IntegrationResponse(BaseModel):
    """Safe integration metadata; credential plaintext and ciphertext are excluded."""

    integration_id: str
    environment: str
    shortcode: str | None
    party_b_shortcode: str | None
    product_type: str | None
    status: str
    credential_status: str
    credentials_validated_at: datetime | None
    c2b_enabled: bool
    c2b_registration_status: str
    stk_callback_url: str | None
    c2b_validation_url: str | None
    c2b_confirmation_url: str | None


def _to_response(record: DarajaIntegration) -> IntegrationResponse:
    """Map a database record to the intentionally secret-free API contract."""
    return IntegrationResponse(
        integration_id=record.integration_id,
        environment=record.environment,
        shortcode=record.shortcode,
        party_b_shortcode=record.party_b_shortcode,
        product_type=record.product_type,
        status=record.status,
        credential_status=record.credential_status,
        credentials_validated_at=record.credentials_validated_at,
        c2b_enabled=record.c2b_enabled,
        c2b_registration_status=record.c2b_registration_status,
        stk_callback_url=record.stk_callback_url,
        c2b_validation_url=record.c2b_validation_url,
        c2b_confirmation_url=record.c2b_confirmation_url,
    )


def _callback_origin(base_url: str, *, production: bool) -> str:
    """Validate a public origin before generating provider callback URLs."""
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(status_code=503, detail="public_callback_origin_invalid")
    if production and parsed.scheme != "https":
        raise HTTPException(status_code=503, detail="production_callbacks_require_https")
    return base_url.rstrip("/")


@router.post(
    "",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate and create a Daraja integration",
)
async def create_integration(
    body: IntegrationCreateRequest,
    principal: MachinePrincipal = Depends(require_scopes("integrations:write")),
    session: AsyncSession = Depends(get_session),
) -> IntegrationResponse:
    """Validate Daraja OAuth credentials, encrypt them, then persist active integration."""
    settings = get_settings()
    encryption_key = settings.credential_encryption_key
    if encryption_key is None or not encryption_key.get_secret_value():
        raise HTTPException(status_code=503, detail="credential_encryption_not_configured")
    origin = _callback_origin(
        settings.public_api_base_url,
        production=body.environment == "production",
    )

    existing_result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.provider == "daraja",
            DarajaIntegration.environment == body.environment,
            DarajaIntegration.deleted_at.is_(None),
        )
    )
    if existing_result.first() is not None:
        raise HTTPException(status_code=409, detail="integration_already_exists_for_environment")

    try:
        consumer_key_ciphertext = encrypt_credential(body.consumer_key.get_secret_value(), key=encryption_key)
        consumer_secret_ciphertext = encrypt_credential(body.consumer_secret.get_secret_value(), key=encryption_key)
        passkey_ciphertext = encrypt_credential(body.passkey.get_secret_value(), key=encryption_key)
    except CredentialEncryptionError:
        raise HTTPException(status_code=503, detail="credential_encryption_not_configured") from None

    try:
        await validate_daraja_credentials(
            environment=body.environment,
            consumer_key=body.consumer_key.get_secret_value(),
            consumer_secret=body.consumer_secret.get_secret_value(),
            timeout_seconds=settings.daraja_timeout_seconds,
        )
    except DarajaCredentialsRejected:
        raise HTTPException(status_code=422, detail="daraja_credentials_invalid") from None
    except DarajaUnavailable:
        raise HTTPException(status_code=503, detail="daraja_authorization_unavailable") from None

    integration_id = "int_" + uuid4().hex
    record = DarajaIntegration(
        merchant_id=principal.merchant_id,
        provider="daraja",
        environment=body.environment,
        status="active",
        integration_id=integration_id,
        shortcode=body.shortcode,
        party_b_shortcode=body.party_b_shortcode or body.shortcode,
        product_type=body.product_type,
        consumer_key_ciphertext=consumer_key_ciphertext,
        consumer_secret_ciphertext=consumer_secret_ciphertext,
        passkey_ciphertext=passkey_ciphertext,
        credential_status="valid",
        credentials_validated_at=datetime.now(UTC),
        c2b_enabled=False,
        c2b_registration_status="not_requested",
        stk_callback_url=origin + "/v1/callbacks/stk/" + integration_id,
        c2b_validation_url=origin + "/v1/callbacks/c2b/validation/" + integration_id,
        c2b_confirmation_url=origin + "/v1/callbacks/c2b/confirmation/" + integration_id,
    )
    audit = AuditLog(
        merchant_id=principal.merchant_id,
        actor_type="machine",
        action="integration.created",
        resource_type="daraja_integration",
        resource_id=record.id,
        metadata_json={
            "integration_id": integration_id,
            "environment": body.environment,
            "shortcode": body.shortcode,
            "product_type": body.product_type,
        },
    )
    session.add(record)
    session.add(audit)
    try:
        await session.flush()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="integration_conflict") from None
    return _to_response(record)


@router.get("", response_model=list[IntegrationResponse], summary="List this merchant's integrations")
async def list_integrations(
    principal: MachinePrincipal = Depends(require_scopes("integrations:read")),
    session: AsyncSession = Depends(get_session),
) -> list[IntegrationResponse]:
    """List only integrations owned by the authenticated merchant."""
    result = await session.exec(
        select(DarajaIntegration)
        .where(
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.deleted_at.is_(None),
        )
        .order_by(DarajaIntegration.created_at.desc())
    )
    return [_to_response(record) for record in result.all()]


@router.get("/{integration_id}", response_model=IntegrationResponse, summary="Inspect one merchant integration")
async def get_integration(
    integration_id: str,
    principal: MachinePrincipal = Depends(require_scopes("integrations:read")),
    session: AsyncSession = Depends(get_session),
) -> IntegrationResponse:
    """Read an integration only when it belongs to the authenticated merchant."""
    result = await session.exec(
        select(DarajaIntegration).where(
            DarajaIntegration.integration_id == integration_id,
            DarajaIntegration.merchant_id == principal.merchant_id,
            DarajaIntegration.deleted_at.is_(None),
        )
    )
    record = result.first()
    if record is None:
        raise HTTPException(status_code=404, detail="integration_not_found")
    return _to_response(record)
