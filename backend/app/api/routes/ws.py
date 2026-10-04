"""Authenticated WebSocket for live SPA updates (NetPay → browser only)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import logger
from app.services.live_hub import subscribe, unsubscribe
from app.services.nethub_auth import NetHubAuthError, fetch_principal

router = APIRouter(tags=["ws"])


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    if not token:
        await websocket.close(code=4401)
        return
    try:
        principal = await fetch_principal(token)
    except NetHubAuthError:
        await websocket.close(code=4401)
        return
    if not principal.is_active:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    q = await subscribe(
        user_id=principal.id,
        tenant_id=principal.tenant_id,
        is_admin=principal.is_admin,
    )

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
