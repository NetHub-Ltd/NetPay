"""FastAPI dependencies for human (IdP → NetHubKe) authentication and membership."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.identity.membership import require_membership
from app.identity.nethub_client import NetHubIdentityError, resolve_human
from app.identity.principal import HumanPrincipal
from app.models.merchants import MerchantMember


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer_token_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer_token_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_human_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> HumanPrincipal:
    """
    Human routes only: forward IdP Bearer to NetHubKe.
    Do not use for M2M merchant APIs (see payments.security.require_scopes).
    """
    token = _bearer_token(authorization)
    try:
        principal = await resolve_human(token)
    except NetHubIdentityError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
        ) from exc
    if not principal.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_disabled")
    return principal


def require_merchant_member(merchant_id_param: str = "merchant_id"):
    """Build a dependency that requires human auth + active membership for a path merchant_id."""

    async def dependency(
        principal: Annotated[HumanPrincipal, Depends(get_human_principal)],
        session: Annotated[AsyncSession, Depends(get_session)],
        merchant_id: UUID,
    ) -> tuple[HumanPrincipal, MerchantMember]:
        # FastAPI injects merchant_id from path when the route declares it
        member = await require_membership(
            session, user_id=principal.id, merchant_id=merchant_id
        )
        return principal, member

    return dependency


async def require_platform_admin(
    principal: Annotated[HumanPrincipal, Depends(get_human_principal)],
) -> HumanPrincipal:
    """NetHubKe is_admin flag — for controlled membership bootstrap only."""
    if not principal.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="platform_admin_required")
    return principal
