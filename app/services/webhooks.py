from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.crud.webhook import webhook_crud, webhook_delivery_crud


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
            raise RuntimeError(f"Webhook liveness failed: HTTP {res.status_code}")
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
) -> None:
    hooks = await webhook_crud.list_by_tenant(session, tenant_id)
    for h in hooks:
        delivery = await deliver_webhook(h.url, h.secret, payload)
        await webhook_delivery_crud.create(
            session,
            obj_in={
                "webhook_id": h.id,
                "payment_intent_id": intent_id,
                "status_code": delivery.get("status"),
                "ok": bool(delivery.get("ok")),
                "error": delivery.get("error"),
            },
        )
    await session.commit()
