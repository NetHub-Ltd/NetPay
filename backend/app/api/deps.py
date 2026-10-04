from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.schemas.principal import Principal
from app.services.nethub_auth import NetHubAuthError, fetch_principal

bearer_scheme = HTTPBearer(auto_error=False)


async def require_internal_api_key(
    x_internal_api_key: Annotated[Optional[str], Header()] = None,
) -> None:
    if not x_internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-Api-Key",
        )


async def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> Principal:
    """
    Resolve the caller via NetHub GET /users/me using the Bearer token as-is.
    NetPay does not decode the token or load a local user row.
    """
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        principal = await fetch_principal(creds.credentials)
    except NetHubAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not principal.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return principal


async def require_admin(
    user: Annotated[Principal, Depends(get_current_user)],
) -> Principal:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def can_access_tenant(user: Principal, tenant_id: UUID) -> bool:
    if user.is_admin:
        return True
    return user.tenant_id is not None and user.tenant_id == tenant_id
