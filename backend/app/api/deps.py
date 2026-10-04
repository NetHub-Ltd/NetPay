from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.crud.tenant import tenant_crud
from app.crud.user import user_crud
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
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Principal:
    """
    Resolve via NetHub GET /users/me. If NetHub has no tenant_id, use NetPay
    local user mapping (primary business).
    """
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        principal = await fetch_principal(creds.credentials)
    except NetHubAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not principal.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    if principal.tenant_id is None and not principal.is_admin:
        local = await user_crud.get_active_by_id(session, principal.id)
        if local is None:
            local = await user_crud.get_by_email(session, principal.email)
        if local and local.tenant_id:
            principal = principal.model_copy(update={"tenant_id": local.tenant_id})

    return principal


async def require_admin(
    user: Annotated[Principal, Depends(get_current_user)],
) -> Principal:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


async def user_can_access_tenant(
    session: AsyncSession,
    user: Principal,
    tenant_id: UUID,
) -> bool:
    if user.is_admin:
        return True
    if user.tenant_id is not None and user.tenant_id == tenant_id:
        return True
    t = await tenant_crud.get(session, tenant_id)
    if t is None or getattr(t, "deleted_at", None) is not None:
        return False
    return t.created_by == user.id


def can_access_tenant(user: Principal, tenant_id: UUID) -> bool:
    """Sync check without DB — NetHub tenant_id or admin only.

    Prefer user_can_access_tenant when ownership via created_by must be allowed.
    """
    if user.is_admin:
        return True
    return user.tenant_id is not None and user.tenant_id == tenant_id
