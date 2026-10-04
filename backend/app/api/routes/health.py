from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.redis import redis_healthy
from app.schemas.health import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    redis_ok = await redis_healthy()
    redis_status = (
        "ok"
        if redis_ok
        else ("required_missing" if settings.redis_required else "optional_unavailable")
    )
    identity_ready = bool((settings.nethub_api_base_url or "").strip())
    status = (
        "ok"
        if db_ok and identity_ready and (redis_ok or not settings.redis_required)
        else "degraded"
    )
    return HealthOut(
        status=status,
        database=db_ok,
        redis=redis_status,
        admin_ready=identity_ready,
        environment=settings.environment,
        version=settings.app_version,
    )


@router.get("/config.json")
async def public_spa_config() -> dict[str, str | bool]:
    """Public SPA bootstrap config (no secrets).

    OIDC values come from runtime env so one container image works everywhere.
    The browser never receives a client secret (PKCE public client only).
    """
    issuer = (settings.oidc_issuer or "").strip().rstrip("/")
    client_id = (settings.oidc_client_id or "").strip()
    redirect = (settings.oidc_redirect_uri or "").strip()
    scopes = (settings.oidc_scopes or "").strip() or "openid profile email offline_access"
    configured = bool(issuer and client_id and issuer != "https://build-placeholder.invalid")
    return {
        "oidc_issuer": issuer,
        "oidc_client_id": client_id,
        "oidc_redirect_uri": redirect,
        "oidc_scopes": scopes,
        "oidc_configured": configured,
        "nethub_api_configured": bool((settings.nethub_api_base_url or "").strip()),
        "environment": settings.environment,
        "version": settings.app_version,
    }

