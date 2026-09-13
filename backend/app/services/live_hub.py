"""In-process live event hub for authenticated SPA clients (no edge polling)."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from app.core.logging import logger

_subscribers: set[asyncio.Queue[str]] = set()
_lock = asyncio.Lock()


async def subscribe() -> asyncio.Queue[str]:
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
    async with _lock:
        _subscribers.add(q)
    return q


async def unsubscribe(q: asyncio.Queue[str]) -> None:
    async with _lock:
        _subscribers.discard(q)


async def publish(event_type: str, payload: dict[str, Any] | None = None) -> None:
    message = json.dumps({"type": event_type, "payload": payload or {}})
    async with _lock:
        targets = list(_subscribers)
    dead: list[asyncio.Queue[str]] = []
    for q in targets:
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(q)
        except Exception as exc:  # noqa: BLE001
            logger.warning("live_hub publish skip: {}", exc)
            dead.append(q)
    if dead:
        async with _lock:
            for q in dead:
                _subscribers.discard(q)


async def publish_edge_connection(snapshot: dict[str, Any]) -> None:
    await publish("edge.connection", snapshot)
