"""Redis pub/sub bus for cross-process live SPA events.

Every API process subscribes; publishers call publish_live() which
PUBLISHes to Redis and also fans out locally (so single-instance works
even if the subscriber loop is delayed).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from app.core.logging import logger
from app.core.redis import get_redis
from app.services import live_hub

LIVE_CHANNEL = "netpay:live"

_subscriber_task: asyncio.Task | None = None
_stop = asyncio.Event()


async def publish_live(event_type: str, payload: dict[str, Any] | None = None) -> None:
    """Broadcast via Redis; subscriber on each process delivers locally.

    If Redis is down, fan out only on this process so single-instance still works.
    """
    body = payload or {}
    message = {"type": event_type, "payload": body}
    raw = json.dumps(message, default=str)

    client = await get_redis()
    if client:
        try:
            await client.publish(LIVE_CHANNEL, raw)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("live Redis publish failed, local fallback: {}", exc)

    try:
        await live_hub.deliver_local(event_type, body)
    except Exception as exc:  # noqa: BLE001
        logger.warning("live local deliver failed: {}", exc)


async def _handle_incoming(raw: str) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    event_type = data.get("type") or "message"
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    # Deliver locally; publishers already delivered once — clients may get duplicates.
    # live_hub queues are small; frontend dedupes by intent_id+status+ts.
    try:
        await live_hub.deliver_local(str(event_type), payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("live subscriber deliver failed: {}", exc)


async def _subscriber_loop() -> None:
    backoff = 1.0
    while not _stop.is_set():
        client = await get_redis()
        if not client:
            try:
                await asyncio.wait_for(_stop.wait(), timeout=min(backoff, 15.0))
            except asyncio.TimeoutError:
                pass
            backoff = min(backoff * 1.5, 15.0)
            continue
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(LIVE_CHANNEL)
            logger.info("live_bus subscribed to Redis channel {}", LIVE_CHANNEL)
            backoff = 1.0
            while not _stop.is_set():
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg is None:
                    await asyncio.sleep(0.05)
                    continue
                if msg.get("type") != "message":
                    continue
                data = msg.get("data")
                if isinstance(data, bytes):
                    data = data.decode("utf-8", errors="replace")
                if isinstance(data, str):
                    await _handle_incoming(data)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("live_bus subscriber error: {}", exc)
            await asyncio.sleep(min(backoff, 15.0))
            backoff = min(backoff * 1.5, 15.0)
        finally:
            try:
                await pubsub.unsubscribe(LIVE_CHANNEL)
                await pubsub.aclose()
            except Exception:  # noqa: BLE001
                pass


async def start_live_subscriber() -> None:
    global _subscriber_task
    _stop.clear()
    if _subscriber_task and not _subscriber_task.done():
        return
    _subscriber_task = asyncio.create_task(_subscriber_loop(), name="netpay-live-bus")


async def stop_live_subscriber() -> None:
    global _subscriber_task
    _stop.set()
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
        except Exception:  # noqa: BLE001
            pass
        _subscriber_task = None
