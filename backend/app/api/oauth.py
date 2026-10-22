"""OAuth-style client-credentials endpoint for merchant-scoped machine clients."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.machine_auth import MachinePrincipal, get_machine_principal, issue_machine_access_token, verify_client_secret
from app.models.merchants import M2MClient, Merchant

router = APIRouter(prefix="/v1/oauth", tags=["machine authentication"])


class TokenRequest(BaseModel):
    """Client-credentials grant request; plaintext secret is never logged."""

    grant_type: Literal["client_credentials"]
    client_id: str = Field(min_length=8, max_length=80)
    client_secret: SecretStr = Field(min_length=32, max_length=256)


class TokenResponse(BaseModel):
    """Short-lived bearer token response."""

    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    scope: str


class MachineIdentityResponse(BaseModel):
    """Safe identity information for confirming the authenticated M2M context."""

    client_id: str
    merchant_id: str
    scope: list[str]


@router.post("/token", response_model=TokenResponse, summary="Issue a machine access token")
async def create_access_token(
    body: TokenRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate a stored client secret and issue a short-lived access token."""
    invalid_client = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "invalid_client"},
        headers={"WWW-Authenticate": 'Basic realm="netpay-token"'},
    )
    try:
        settings = get_settings()
        client_result = await session.exec(
            select(M2MClient).where(
                M2MClient.client_id == body.client_id,
                M2MClient.deleted_at.is_(None),
            )
        )
        client = client_result.first()
        if client is None or client.status != "active" or client.revoked_at is not None:
            raise invalid_client
        now = datetime.now(UTC)
        if client.expires_at is not None and client.expires_at <= now:
            raise invalid_client
        merchant_result = await session.exec(
            select(Merchant).where(
                Merchant.id == client.merchant_id,
                Merchant.deleted_at.is_(None),
            )
        )
        merchant = merchant_result.first()
        if merchant is None or merchant.status != "active":
            raise invalid_client
        if not verify_client_secret(body.client_secret.get_secret_value(), client.secret_hash):
            raise invalid_client
        token = issue_machine_access_token(
            client_id=client.client_id,
            merchant_id=client.merchant_id,
            scopes=client.scopes,
            settings=settings,
            now=now,
        )
        client.last_used_at = now
        await session.commit()
        return TokenResponse(
            access_token=token,
            expires_in=settings.machine_token_ttl_minutes * 60,
            scope=" ".join(sorted(set(client.scopes))),
        )
    except HTTPException:
        raise
    except (RuntimeError, ValueError):
        raise HTTPException(status_code=503, detail="machine_auth_not_configured") from None


@router.get("/me", response_model=MachineIdentityResponse, summary="Inspect current machine identity")
async def current_machine_identity(
    principal: MachinePrincipal = Depends(get_machine_principal),
) -> MachineIdentityResponse:
    """Return the authenticated client and scope context without exposing secrets."""
    return MachineIdentityResponse(
        client_id=principal.client_id,
        merchant_id=str(principal.merchant_id),
        scope=sorted(principal.scopes),
    )
