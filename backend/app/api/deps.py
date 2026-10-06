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
    Resolve identity from:
    1. NetPay machine JWT (client_credentials) — typ=machine
    2. Else NetHub GET /users/me for human sessions
    """
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = creds.credentials

    # Machine JWT issued by NetPay /v1/oauth/token
    machine = _try_machine_principal(token)
    if machine is not None:
        if not machine.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client disabled")
        return machine

    try:
        principal = await fetch_principal(token)
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


def _try_machine_principal(token: str) -> Principal | None:
    """Return Principal if token is a valid NetPay machine JWT; else None."""
    from uuid import UUID, uuid5, NAMESPACE_URL

    from jose import JWTError

    from app.core.security import decode_token

    try:
        payload = decode_token(token)
    except JWTError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("typ") != "machine":
        return None
    client_id = payload.get("client_id") or payload.get("sub")
    tenant_raw = payload.get("tenant_id")
    if not client_id or not tenant_raw:
        return None
    try:
        tenant_id = UUID(str(tenant_raw))
    except ValueError:
        return None
    # Stable synthetic id for Principal.id (not a human user)
    pid = uuid5(NAMESPACE_URL, f"netpay:machine:{client_id}")
    return Principal(
        id=pid,
        email=f"{client_id}@clients.netpay.local",
        full_name=str(payload.get("name") or client_id),
        username=str(client_id),
        is_active=True,
        tenant_id=tenant_id,
        is_admin=False,
        client_id=str(client_id),
    )


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
