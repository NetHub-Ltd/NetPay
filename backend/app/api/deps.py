"""Request dependencies.

Auth model (locked):
  Keycloak authenticates the client.
  NetPay forwards the Bearer token to NetHub API for authorization + context.
  NetPay does not validate Keycloak JWKS and does not trust JWT claims for business data.
"""
from __future__ import annotations

import hashlib
import time
from typing import Annotated, Any, Optional
from uuid import UUID

import httpx
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.logging import logger
from app.core.security import decode_test_token, subject_as_uuid
from app.crud.user import user_crud
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

# Process-local context cache: token_hash -> (expires_at, context_dict)
_context_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _token_cache_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _cache_get(token: str) -> Optional[dict[str, Any]]:
    ttl = settings.nethub_context_cache_ttl_sec
    if ttl <= 0:
        return None
    key = _token_cache_key(token)
    row = _context_cache.get(key)
    if not row:
        return None
    expires_at, ctx = row
    if time.time() >= expires_at:
        _context_cache.pop(key, None)
        return None
    return ctx


def _cache_set(token: str, ctx: dict[str, Any]) -> None:
    ttl = settings.nethub_context_cache_ttl_sec
    if ttl <= 0:
        return
    key = _token_cache_key(token)
    _context_cache[key] = (time.time() + ttl, ctx)
    # Bound cache size
    if len(_context_cache) > 2048:
        oldest = sorted(_context_cache.items(), key=lambda kv: kv[1][0])[:512]
        for k, _ in oldest:
            _context_cache.pop(k, None)


async def require_internal_api_key(
    x_internal_api_key: Annotated[Optional[str], Header()] = None,
) -> None:
    if not x_internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-Api-Key",
        )


async def _fetch_nethub_context(token: str) -> dict[str, Any]:
    """
    Ask NetHub API who this token is and what they may access.
    NetHub validates the Keycloak token; NetPay does not.
    """
    cached = _cache_get(token)
    if cached is not None:
        return cached

    base = (settings.nethub_api_base_url or "").rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NETHUB_API_BASE_URL is not configured",
        )

    headers = {"Authorization": f"Bearer {token}"}
    url_me = f"{base}/api/v1/users/me"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url_me, headers=headers)
            if res.status_code == 404:
                sync = await client.post(f"{base}/api/v1/users/sync", headers=headers)
                if sync.status_code in (401, 403):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="NetHub rejected token",
                    )
                if sync.status_code >= 400:
                    logger.warning("NetHub sync failed status={}", sync.status_code)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User not provisioned in NetHub",
                    )
                res = await client.get(url_me, headers=headers)
            if res.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="NetHub rejected token",
                )
            if res.status_code >= 400:
                logger.warning("NetHub /users/me failed status={}", res.status_code)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="NetHub context unavailable",
                )
            ctx = res.json()
            _cache_set(token, ctx)
            return ctx
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("NetHub context fetch error: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="NetHub context unavailable",
        ) from exc


def _context_to_binding(ctx: dict[str, Any]) -> dict[str, Any]:
    """Map NetHub /users/me payload into local binding fields. No JWT claims used."""
    email = (ctx.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=502, detail="NetHub context missing email")

    # keycloak_id / sub from NetHub profile, not from raw JWT
    raw_sub = ctx.get("keycloak_id") or ctx.get("sub") or ctx.get("id")
    keycloak_id: Optional[UUID] = None
    if raw_sub:
        try:
            keycloak_id = UUID(str(raw_sub))
        except ValueError:
            keycloak_id = None

    tenant_id: Optional[UUID] = None
    tenant = ctx.get("tenant")
    if isinstance(tenant, dict) and tenant.get("id"):
        try:
            tenant_id = UUID(str(tenant["id"]))
        except ValueError:
            tenant_id = None
    elif ctx.get("tenant_id"):
        try:
            tenant_id = UUID(str(ctx["tenant_id"]))
        except ValueError:
            tenant_id = None

    roles = ctx.get("roles") or []
    if isinstance(roles, str):
        roles = roles.split()
    role = "admin" if any(str(r).lower() == "admin" for r in roles) else "user"
    # NetHub may expose an explicit role field
    if ctx.get("role") in ("admin", "user"):
        role = ctx["role"]

    return {
        "email": email,
        "keycloak_id": keycloak_id,
        "display_name": ctx.get("full_name") or ctx.get("username") or ctx.get("display_name"),
        "role": role,
        "tenant_id": tenant_id,
        "is_active": bool(ctx.get("is_active", True)),
    }


async def _upsert_local_binding(session: AsyncSession, binding: dict[str, Any]) -> User:
    """
    Disposable local row for FKs / can_access_tenant.
    Not a source of truth — NetHub context wins on every refresh.
    """
    user = None
    if binding.get("keycloak_id"):
        user = await user_crud.get_by_keycloak_id(session, binding["keycloak_id"])
    if user is None:
        user = await user_crud.get_by_email(session, binding["email"])

    payload = {
        "email": binding["email"],
        "keycloak_id": binding.get("keycloak_id"),
        "display_name": binding.get("display_name"),
        "role": binding.get("role") or "user",
        "tenant_id": binding.get("tenant_id"),
        "is_active": binding.get("is_active", True),
        "hashed_password": None,
    }
    if user is None:
        user = await user_crud.create(session, obj_in=payload)
    else:
        user = await user_crud.update(session, db_obj=user, obj_in=payload)
    await session.commit()
    await session.refresh(user)
    return user


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> User:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    token = creds.credentials

    # --- Local M2M client_credentials (NetPay-issued HS256, not Keycloak) ---
    try:
        from jose import jwt as jose_jwt
        from jose import JWTError
        peek = jose_jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        if peek.get("m2m"):
            from app.crud.oauth_client import oauth_client_crud

            client_id = peek.get("client_id")
            if not client_id:
                raise HTTPException(status_code=401, detail="Invalid M2M token")
            client = await oauth_client_crud.get_active_by_client_id(
                session, str(client_id)
            )
            if not client:
                raise HTTPException(status_code=401, detail="Unknown M2M client")
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
    except JWTError:
        pass  # not a NetPay M2M token — continue to NetHub path
    except HTTPException:
        raise

    # --- Production / normal path: NetHub is the authority ---
    if settings.nethub_api_base_url:
        ctx = await _fetch_nethub_context(token)
        binding = _context_to_binding(ctx)
        user = await _upsert_local_binding(session, binding)
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")
        return user

    # --- Test-only fallback when NetHub URL is unset ---
    if not settings.is_test:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NETHUB_API_BASE_URL is required",
        )

    payload = decode_test_token(token)
    if payload.get("m2m"):
        raise HTTPException(status_code=401, detail="Invalid M2M token")

    sub = subject_as_uuid(payload.get("sub"))
    user = await user_crud.get_by_keycloak_id(session, sub)
    if user is None:
        email = (payload.get("email") or f"{sub}@nethub.local").lower()
        user = await user_crud.get_by_email(session, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not provisioned (test seed missing)",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
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
