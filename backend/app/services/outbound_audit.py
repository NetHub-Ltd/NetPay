"""Persist and log every outbound provider HTTP call."""
from __future__ import annotations

import json
import time
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.outbound_request import OutboundRequest

SENSITIVE_KEYS = frozenset({"password", "Password", "passkey", "Passkey", "consumer_secret", "ConsumerSecret"})


def redact_provider_payload(obj: Any) -> Any:
    """Deep-copy structure with sensitive Daraja fields redacted for storage."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in SENSITIVE_KEYS or k.lower() in {"password", "passkey", "consumer_secret"}:
                out[k] = "***REDACTED***"
            else:
                out[k] = redact_provider_payload(v)
        return out
    if isinstance(obj, list):
        return [redact_provider_payload(x) for x in obj]
    return obj


def _clip(text: str | None, n: int = 4000) -> str | None:
    if text is None:
        return None
    return text if len(text) <= n else text[:n] + "…"


async def record_outbound(
    session: Optional[AsyncSession],
    *,
    provider: str,
    operation: str,
    method: str,
    url: str,
    request_body: Any = None,
    response: httpx.Response | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
) -> None:
    req_s = None
    if request_body is not None:
        safe = redact_provider_payload(request_body)
        req_s = _clip(safe if isinstance(safe, str) else json.dumps(safe, default=str))

    status = response.status_code if response is not None else None
    body = _clip(response.text if response is not None else None)
    success = bool(response is not None and response.status_code < 400 and not error)

    logger.bind(operation=operation, provider=provider).log(
        "INFO" if success else "ERROR",
        "outbound {} {} {} status={} duration_ms={} intent={} err={} body={}",
        method,
        operation,
        url,
        status,
        duration_ms,
        payment_intent_id,
        error,
        (body or "")[:500],
    )

    try:
        from app.core.db import AsyncSessionLocal

        async with AsyncSessionLocal() as audit_session:
            row = OutboundRequest(
                tenant_id=tenant_id,
                integration_id=integration_id,
                payment_intent_id=payment_intent_id,
                provider=provider,
                operation=operation,
                method=method,
                url=url[:1024],
                request_body=req_s,
                response_status=status,
                response_body=body,
                success=success,
                error_message=(error or "")[:1024] if error else None,
                duration_ms=duration_ms,
            )
            audit_session.add(row)
            await audit_session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to persist outbound_request: {}", exc)


async def provider_request(
    session: Optional[AsyncSession],
    *,
    method: str,
    url: str,
    operation: str,
    provider: str = "mpesa",
    headers: dict | None = None,
    json_body: Any = None,
    timeout: float = 30.0,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
) -> httpx.Response:
    """Perform HTTP call; always log; always try to audit-row (password redacted)."""
    t0 = time.perf_counter()
    response: httpx.Response | None = None
    err: str | None = None
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, headers=headers or {}, json=json_body)
        return response
    except Exception as exc:  # noqa: BLE001
        err = str(exc)[:1024]
        logger.exception("outbound transport failure {} {}: {}", operation, url, exc)
        raise
    finally:
        ms = int((time.perf_counter() - t0) * 1000)
        await record_outbound(
            session,
            provider=provider,
            operation=operation,
            method=method,
            url=url,
            request_body=json_body,
            response=response,
            error=err,
            duration_ms=ms,
            tenant_id=tenant_id,
            integration_id=integration_id,
            payment_intent_id=payment_intent_id,
        )
