from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

import httpx
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.logging import logger
from app.core.security import decode_access_token, subject_as_uuid
from app.crud.user import user_crud
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def require_internal_api_key(
    x_internal_api_key: Annotated[Optional[str], Header()] = None,
) -> None:
    if not x_internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-Api-Key",
        )


async def _fetch_nethub_context(token: str, sub: UUID) -> Optional[dict]:
    """Call NetHub API GET /api/v1/users/me with the same Keycloak token."""
    base = (settings.nethub_api_base_url or "").rstrip("/")
    if not base:
        return None
    url = f"{base}/api/v1/users/me"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if res.status_code == 404:
                # First-time user — ask NetHub to sync, then retry once
                sync = await client.post(
                    f"{base}/api/v1/users/sync",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if sync.status_code >= 400:
                    logger.warning(
                        "NetHub sync failed sub={} status={}", sub, sync.status_code
                    )
                    return None
                res = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if res.status_code == 401 or res.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="NetHub denied access for this token",
                )
            if res.status_code >= 400:
                logger.warning(
                    "NetHub /users/me failed sub={} status={}", sub, res.status_code
                )
                return None
            return res.json()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("NetHub context fetch error sub={} err={}", sub, exc)
        return None


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> User:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_access_token(creds.credentials)

    # M2M client_credentials tokens (local oauth) — not Keycloak user SSO
    if payload.get("m2m"):
        from app.crud.oauth_client import oauth_client_crud
        client_id = payload.get("client_id")
        if not client_id:
            raise HTTPException(status_code=401, detail="Invalid M2M token")
        client = await oauth_client_crud.get_active_by_client_id(session, str(client_id))
        if not client:
            raise HTTPException(status_code=401, detail="Unknown M2M client")
        # Synthetic user row for downstream can_access_tenant checks
        email = f"{client.client_id}@m2m.local"
        user = await user_crud.get_by_email(session, email)
        if user is None:
            user = await user_crud.create(
                session,
                obj_in={
                    "email": email,
                    "role": "user",
                    "tenant_id": client.tenant_id,
                    "is_active": True,
                    "hashed_password": None,
                    "display_name": client.name or client.client_id,
                },
            )
            await session.commit()
            await session.refresh(user)
        return user

    sub = subject_as_uuid(payload)

    user = await user_crud.get_by_keycloak_id(session, sub)

    # Optional enrichment from NetHub API (same token).
    ctx = await _fetch_nethub_context(creds.credentials, sub)
    if ctx:
        email = (ctx.get("email") or payload.get("email") or f"{sub}@nethub.local").lower()
        display = ctx.get("full_name") or ctx.get("username") or payload.get("name")
        # Tenant from NetHub context if present
        tenant_raw = None
        if isinstance(ctx.get("tenant"), dict):
            tenant_raw = ctx["tenant"].get("id")
        elif ctx.get("tenant_id"):
            tenant_raw = ctx.get("tenant_id")
        tenant_id: Optional[UUID] = None
        if tenant_raw:
            try:
                tenant_id = UUID(str(tenant_raw))
            except ValueError:
                tenant_id = None

        if user is None:
            user = await user_crud.create(
                session,
                obj_in={
                    "email": email,
                    "keycloak_id": sub,
                    "display_name": display,
                    "role": "admin" if "admin" in (ctx.get("roles") or []) else "user",
                    "tenant_id": tenant_id,
                    "is_active": bool(ctx.get("is_active", True)),
                    "hashed_password": None,
                },
            )
            await session.commit()
            await session.refresh(user)
        else:
            updates: dict = {}
            if email and user.email != email:
                updates["email"] = email
            if display and user.display_name != display:
                updates["display_name"] = display
            if tenant_id and user.tenant_id != tenant_id:
                updates["tenant_id"] = tenant_id
            if updates:
                user = await user_crud.update(session, db_obj=user, obj_in=updates)
                await session.commit()
                await session.refresh(user)

    if user is None:
        # Local-only binding (tests / NetHub URL not configured)
        email = (payload.get("email") or f"{sub}@nethub.local").lower()
        user = await user_crud.get_by_email(session, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not provisioned in NetPay; complete NetHub profile first",
            )
        if user.keycloak_id is None:
            user = await user_crud.update(
                session, db_obj=user, obj_in={"keycloak_id": sub}
            )
            await session.commit()
            await session.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return user


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def can_access_tenant(user: User, tenant_id: UUID) -> bool:
    if user.role == "admin":
        return True
    return user.tenant_id == tenant_id
