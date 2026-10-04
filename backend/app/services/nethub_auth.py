"""Resolve the caller via NetHub API — NetPay does not decode or store users."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import logger
from app.schemas.principal import Principal


class NetHubAuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


def _admin_emails() -> set[str]:
    raw = (settings.admin_email or "").strip().lower()
    extra = (getattr(settings, "admin_emails", None) or "").strip()
    emails = {raw} if raw else set()
    if extra:
        emails.update(e.strip().lower() for e in extra.split(",") if e.strip())
    return emails


async def fetch_principal(access_token: str) -> Principal:
    """
    Call NetHub GET /api/v1/users/me with the caller's Bearer token.
    NetPay never validates or decodes the JWT.
    """
    base = (settings.nethub_api_base_url or "").rstrip("/")
    if not base:
        raise NetHubAuthError(
            "NETHUB_API_BASE_URL is not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    url = f"{base}/api/v1/users/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    timeout = httpx.Timeout(settings.nethub_api_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        logger.error("NetHub identity request failed: {}", exc)
        raise NetHubAuthError(
            "Identity service unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc

    if resp.status_code in (401, 403):
        raise NetHubAuthError("Invalid or expired token", status_code=401)
    if resp.status_code >= 500:
        logger.error("NetHub identity error status={} body={}", resp.status_code, resp.text[:200])
        raise NetHubAuthError(
            "Identity service error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if resp.status_code != 200:
        logger.warning("NetHub identity unexpected status={}", resp.status_code)
        raise NetHubAuthError("Not authenticated", status_code=401)

    try:
        data: dict[str, Any] = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise NetHubAuthError("Invalid identity response") from exc

    try:
        uid = UUID(str(data["id"]))
    except Exception as exc:  # noqa: BLE001
        raise NetHubAuthError("Invalid identity response") from exc

    email = str(data.get("email") or "").strip().lower()
    if not email:
        raise NetHubAuthError("Identity missing email")

    tenant_id = None
    raw_tid = data.get("tenant_id")
    if raw_tid:
        try:
            tenant_id = UUID(str(raw_tid))
        except Exception:  # noqa: BLE001
            tenant_id = None

    is_active = bool(data.get("is_active", True))
    is_admin = email in _admin_emails()

    return Principal(
        id=uid,
        email=email,
        full_name=str(data.get("full_name") or ""),
        username=str(data.get("username") or ""),
        is_active=is_active,
        tenant_id=tenant_id,
        tenant_name=data.get("tenant_name"),
        tenant_tier=data.get("tenant_tier"),
        is_admin=is_admin,
    )
