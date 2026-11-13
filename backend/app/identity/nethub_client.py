"""Forward IdP access tokens to NetHubKe (resource server). NetPay does not verify JWTs.

Human identity is always the NetHubKe user profile. Successful resolutions may be
cached briefly in Redis (token-hash key) to reduce RS latency; failures are never
cached. Redis outage degrades to live RS calls.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

import httpx
from fastapi import status

from app.core.config import get_settings
from app.identity.principal import HumanPrincipal
from loguru import logger

_CACHE_PREFIX = "netpay:rsuser:v1:"


class NetHubIdentityError(Exception):
    def __init__(self, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


def _base_url() -> str:
    settings = get_settings()
    base = (settings.nethub_api_base_url or "").strip().rstrip("/")
    if not base:
        raise NetHubIdentityError(
            "NETHUB_API_BASE_URL is not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return base


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(get_settings().nethub_api_timeout_seconds)


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _token_cache_key(access_token: str) -> str:
    digest = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}{digest}"


def _principal_to_cache_payload(principal: HumanPrincipal) -> str:
    return json.dumps(
        {
            "id": str(principal.id),
            "email": principal.email,
            "full_name": principal.full_name,
            "username": principal.username,
            "is_active": principal.is_active,
            "is_admin": principal.is_admin,
            "tenant_id": str(principal.tenant_id) if principal.tenant_id else None,
        },
        separators=(",", ":"),
    )


def _principal_from_cache_payload(raw: str) -> HumanPrincipal | None:
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return _parse_user(data)
    except Exception:  # noqa: BLE001
        return None


async def _cache_get(access_token: str) -> HumanPrincipal | None:
    settings = get_settings()
    if not settings.redis_enabled or settings.nethub_user_cache_ttl_seconds <= 0:
        return None
    try:
        from app.core.cache import create_redis_client

        client = create_redis_client(settings)
        try:
            raw = await client.get(_token_cache_key(access_token))
        finally:
            await client.aclose()
        if not raw or not isinstance(raw, str):
            return None
        return _principal_from_cache_payload(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rs_user_cache_get_failed error_type={}", type(exc).__name__)
        return None


async def _cache_set(access_token: str, principal: HumanPrincipal) -> None:
    settings = get_settings()
    ttl = settings.nethub_user_cache_ttl_seconds
    if not settings.redis_enabled or ttl <= 0:
        return
    try:
        from app.core.cache import create_redis_client

        client = create_redis_client(settings)
        try:
            await client.set(
                _token_cache_key(access_token),
                _principal_to_cache_payload(principal),
                ex=ttl,
            )
        finally:
            await client.aclose()
    except Exception as exc:  # noqa: BLE001
        logger.warning("rs_user_cache_set_failed error_type={}", type(exc).__name__)


def _parse_user(data: dict[str, Any]) -> HumanPrincipal:
    try:
        uid = UUID(str(data["id"]))
    except Exception as exc:  # noqa: BLE001
        raise NetHubIdentityError("Invalid identity response") from exc

    email = str(data.get("email") or "").strip().lower()
    if not email:
        raise NetHubIdentityError("Identity missing email")

    tenant_id = None
    raw_tid = data.get("tenant_id")
    if raw_tid:
        try:
            tenant_id = UUID(str(raw_tid))
        except Exception:  # noqa: BLE001
            tenant_id = None

    return HumanPrincipal(
        id=uid,
        email=email,
        full_name=str(data.get("full_name") or ""),
        username=str(data.get("username") or ""),
        is_active=bool(data.get("is_active", True)),
        is_admin=bool(data.get("is_admin", False)),
        tenant_id=tenant_id,
    )


async def _request(method: str, path: str, access_token: str) -> httpx.Response:
    url = f"{_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            return await client.request(method, url, headers=_headers(access_token))
    except httpx.RequestError as exc:
        logger.error("NetHubKe identity request failed path={}", path)
        raise NetHubIdentityError(
            "Identity service unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc


async def sync_user(access_token: str) -> HumanPrincipal:
    """POST /api/v1/users/sync — provision or refresh the RS user from the IdP token."""
    resp = await _request("POST", "/api/v1/users/sync", access_token)
    if resp.status_code in (401, 403):
        raise NetHubIdentityError("Invalid or expired token", status_code=401)
    if resp.status_code >= 500:
        logger.error("NetHubKe sync error status={}", resp.status_code)
        raise NetHubIdentityError(
            "Identity service error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if resp.status_code not in (200, 201):
        logger.warning("NetHubKe sync unexpected status={}", resp.status_code)
        raise NetHubIdentityError("Not authenticated", status_code=401)
    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise NetHubIdentityError("Invalid identity response") from exc
    if not isinstance(data, dict):
        raise NetHubIdentityError("Invalid identity response")
    return _parse_user(data)


async def fetch_me(access_token: str) -> HumanPrincipal:
    """GET /api/v1/users/me — current user; does not auto-sync."""
    resp = await _request("GET", "/api/v1/users/me", access_token)
    if resp.status_code == 404:
        raise NetHubIdentityError("User not provisioned", status_code=404)
    if resp.status_code in (401, 403):
        raise NetHubIdentityError("Invalid or expired token", status_code=401)
    if resp.status_code >= 500:
        logger.error("NetHubKe me error status={}", resp.status_code)
        raise NetHubIdentityError(
            "Identity service error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if resp.status_code != 200:
        logger.warning("NetHubKe me unexpected status={}", resp.status_code)
        raise NetHubIdentityError("Not authenticated", status_code=401)
    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise NetHubIdentityError("Invalid identity response") from exc
    if not isinstance(data, dict):
        raise NetHubIdentityError("Invalid identity response")
    return _parse_user(data)


async def resolve_human(access_token: str) -> HumanPrincipal:
    """
    Resolve human via NetHubKe RS: cache → /me → on 404 /sync then /me.

    Successful principals may be served from Redis within TTL. Auth failures
    are never written to cache. Redis errors degrade to live RS calls.
    """
    cached = await _cache_get(access_token)
    if cached is not None:
        return cached

    try:
        principal = await fetch_me(access_token)
    except NetHubIdentityError as exc:
        if exc.status_code != 404:
            raise
        await sync_user(access_token)
        principal = await fetch_me(access_token)

    await _cache_set(access_token, principal)
    return principal
