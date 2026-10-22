"""Operator-key-protected bootstrap endpoint for merchant M2M clients."""
from __future__ import annotations

import hmac
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.machine_auth import ALLOWED_MACHINE_SCOPES, create_m2m_client
from app.models.merchants import Merchant

router = APIRouter(prefix="/v1/internal", tags=["operator provisioning"])


class M2MClientCreateRequest(BaseModel):
    """Create one merchant-owned machine client with an explicit scope allow-list."""

    merchant_id: UUID
    scopes: list[str] = Field(min_length=1, max_length=len(ALLOWED_MACHINE_SCOPES))
    expires_at: datetime | None = None


class M2MClientCreatedResponse(BaseModel):
    """One-time response containing the newly generated client secret."""

    client_id: str
    client_secret: str
    merchant_id: UUID
    scopes: list[str]
    expires_at: datetime | None


@router.post(
    "/m2m-clients",
    response_model=M2MClientCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a merchant machine client",
)
async def provision_m2m_client(
    body: M2MClientCreateRequest,
    provisioning_key: str | None = Header(default=None, alias="X-NetPay-Provisioning-Key"),
    session: AsyncSession = Depends(get_session),
) -> M2MClientCreatedResponse:
    """Create a client only when an operator-supplied provisioning key is configured."""
    configured_secret = get_settings().m2m_provisioning_key
    expected_key = configured_secret.get_secret_value() if configured_secret is not None else ""
    if len(expected_key) < 32:
        # Hide the endpoint when provisioning has not been explicitly enabled.
        raise HTTPException(status_code=404, detail="not_found")
    if provisioning_key is None or not hmac.compare_digest(provisioning_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_operator_credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    merchant_result = await session.exec(
        select(Merchant).where(
            Merchant.id == body.merchant_id,
            Merchant.deleted_at.is_(None),
        )
    )
    merchant = merchant_result.first()
    if merchant is None or merchant.status != "active":
        raise HTTPException(status_code=404, detail="merchant_not_found")

    try:
        created = await create_m2m_client(
            session,
            merchant_id=merchant.id,
            scopes=body.scopes,
            expires_at=body.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    await session.commit()
    return M2MClientCreatedResponse(
        client_id=created.client.client_id,
        client_secret=created.client_secret,
        merchant_id=merchant.id,
        scopes=created.client.scopes,
        expires_at=created.client.expires_at,
    )
