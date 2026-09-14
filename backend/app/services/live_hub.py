"""In-process WebSocket fanout (per API process). Cross-process via live_bus + Redis."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.logging import logger


@dataclass
class Subscriber:
    queue: asyncio.Queue[str]
    user_id: UUID | None = None
    tenant_id: UUID | None = None
    is_admin: bool = False


_subscribers: list[Subscriber] = []
_lock = asyncio.Lock()


async def subscribe(
    *,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    is_admin: bool = False,
) -> asyncio.Queue[str]:
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
    sub = Subscriber(queue=q, user_id=user_id, tenant_id=tenant_id, is_admin=is_admin)
    async with _lock:
        _subscribers.append(sub)
    return q


async def unsubscribe(q: asyncio.Queue[str]) -> None:
    async with _lock:
        _subscribers[:] = [s for s in _subscribers if s.queue is not q]


def _visible_to(sub: Subscriber, payload: dict[str, Any]) -> bool:
    if sub.is_admin:
        return True
    tid = payload.get("tenant_id")
    if tid is None:
        return True
    if sub.tenant_id is None:
        return False
    return str(sub.tenant_id) == str(tid)


async def deliver_local(event_type: str, payload: dict[str, Any] | None = None) -> None:
    """Fan out to WebSocket queues on this process only."""
    body = payload or {}
    message = json.dumps({"type": event_type, "payload": body}, default=str)
    async with _lock:
        targets = list(_subscribers)
    dead: list[asyncio.Queue[str]] = []
    for sub in targets:
        if not _visible_to(sub, body):
            continue
        try:
            sub.queue.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(sub.queue)
        except Exception as exc:  # noqa: BLE001
            logger.warning("live_hub deliver skip: {}", exc)
            dead.append(sub.queue)
    if dead:
        async with _lock:
            _subscribers[:] = [s for s in _subscribers if s.queue not in dead]


async def publish(event_type: str, payload: dict[str, Any] | None = None) -> None:
    """Preferred entry: Redis bus + local (via live_bus)."""
    from app.services.live_bus import publish_live

    await publish_live(event_type, payload)


async def publish_edge_connection(snapshot: dict[str, Any]) -> None:
    await publish("edge.connection", snapshot)


async def publish_notification(
    *,
    title: str,
    body: str,
    tenant_id: UUID | None = None,
    intent_id: UUID | None = None,
    level: str = "info",
    href: str | None = None,
    status: str | None = None,
) -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    await publish(
        "payment.update",
        {
            "id": f"n_{intent_id or 'sys'}_{uuid4().hex[:10]}",
            "title": title,
            "body": body,
            "level": level,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "intent_id": str(intent_id) if intent_id else None,
            "href": href or (f"/intents/{intent_id}" if intent_id else None),
            "status": status,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
