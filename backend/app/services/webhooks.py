from __future__ import annotations

import hashlib
import hmac
import json
import secrets as pysecrets
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.crud.webhook import webhook_crud, webhook_delivery_crud
from app.models.payment_intent import PaymentIntent


def sign_payload(secret: str, body: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


async def probe_webhook_liveness(url: str, secret: str) -> None:
    payload = json.dumps(
        {"event": "nethub.webhook.probe", "ts": datetime.now(timezone.utc).isoformat()}
    )
    sig = sign_payload(secret, payload)
    timeout = settings.webhook_timeout_seconds
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(
                url,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Nethub-Signature": f"sha256={sig}",
                    "X-Nethub-Event": "nethub.webhook.probe",
                },
            )
        if res.status_code < 200 or res.status_code >= 300:
            logger.warning("Webhook probe failed url={} status={}", url, res.status_code)
            raise RuntimeError(f"Webhook liveness failed: HTTP {res.status_code}")
        logger.info("Webhook probe ok url={} status={}", url, res.status_code)
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Webhook liveness timed out ({timeout}s)") from exc
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Webhook liveness failed: {exc}") from exc


async def deliver_webhook(url: str, secret: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload)
    sig = sign_payload(secret, body)
    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
            res = await client.post(
                url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Nethub-Signature": f"sha256={sig}",
                    "X-Nethub-Event": str(payload.get("event", "payment.update")),
                },
            )
        if res.status_code < 200 or res.status_code >= 300:
            return {"ok": False, "status": res.status_code, "error": f"HTTP {res.status_code}"}
        return {"ok": True, "status": res.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


async def fanout_webhooks(
    session: AsyncSession,
    tenant_id: UUID,
    intent_id: UUID,
    payload: dict[str, Any],
    *,
    intent: Optional[PaymentIntent] = None,
) -> None:
    """
    After payment is resolved:
    1. If intent.status_callback_url → POST once (ephemeral secret for signature)
    2. Else tenant stored webhooks
    3. Else no merchant notify (STK/C2B still always went to edge)
    """
    if intent is None:
        from app.crud.payment_intent import payment_intent_crud

        intent = await payment_intent_crud.get(session, intent_id)

    targets: list[tuple[str, str, UUID | None]] = []
    # (url, secret, webhook_id for delivery log)

    if intent and intent.status_callback_url:
        # Per-intent URL: sign with a one-off secret embedded in payload for verification by partners who share nothing
        # Prefer deterministic HMAC using settings.secret_key + intent id so partner can verify if documented
        secret = hashlib.sha256(f"{settings.secret_key}:{intent_id}".encode()).hexdigest()
        targets.append((intent.status_callback_url, secret, None))
        logger.info("Notify via intent status_callback_url intent={}", intent_id)
    else:
        hooks = await webhook_crud.list_by_tenant(session, tenant_id)
        for h in hooks:
            targets.append((h.url, h.secret, h.id))
        if not targets:
            logger.info("No merchant notify targets for intent={} (edge-only callbacks)", intent_id)
            return

    for url, secret, webhook_id in targets:
        delivery = await deliver_webhook(url, secret, payload)
        if webhook_id is not None:
            await webhook_delivery_crud.create(
                session,
                obj_in={
                    "webhook_id": webhook_id,
                    "payment_intent_id": intent_id,
                    "status_code": delivery.get("status"),
                    "ok": bool(delivery.get("ok")),
                    "error": delivery.get("error"),
                },
            )
        else:
            logger.info(
                "Intent callback delivery intent={} ok={} status={} err={}",
                intent_id,
                delivery.get("ok"),
                delivery.get("status"),
                delivery.get("error"),
            )
    await session.commit()
