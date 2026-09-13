"""Authenticated WebSocket for live SPA updates (NetPay → browser only)."""
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.db import AsyncSessionLocal
from app.core.logging import logger
from app.core.security import decode_token
from app.crud.user import user_crud
from app.services.live_hub import subscribe, unsubscribe

router = APIRouter(tags=["ws"])


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
        uid = UUID(payload["sub"])
    except Exception:  # noqa: BLE001
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as session:
        user = await user_crud.get_active_by_id(session, uid)
        if not user:
            await websocket.close(code=4401)
            return

    await websocket.accept()
    q = await subscribe()

    async def _drain_client() -> None:
        try:
            while True:
                await websocket.receive()
        except WebSocketDisconnect:
            return
        except Exception:
            return

    reader = asyncio.create_task(_drain_client())
    try:
        await websocket.send_json({"type": "connected", "payload": {"ok": True}})
        while True:
            if reader.done():
                break
            try:
                msg = await asyncio.wait_for(q.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # keepalive ping so proxies don't idle-close
                try:
                    await websocket.send_json({"type": "ping", "payload": {}})
                except Exception:
                    break
                continue
            try:
                await websocket.send_text(msg)
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("ws_events error: {}", exc)
    finally:
        reader.cancel()
        await unsubscribe(q)
