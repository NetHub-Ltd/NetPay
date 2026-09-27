"""Authenticated WebSocket for live SPA updates (NetPay → browser only)."""
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.logging import logger
from app.core.security import decode_test_token, subject_as_uuid
from app.crud.user import user_crud
from app.services.live_hub import subscribe, unsubscribe

router = APIRouter(tags=["ws"])


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    """
    Auth: same model as HTTP — production should resolve via NetHub context.
    Test mode uses HS256 test tokens and local keycloak_id binding.
    """
    if not token:
        await websocket.close(code=4401)
        return

    user = None
    try:
        if settings.is_test or not settings.nethub_api_base_url:
            payload = decode_test_token(token)
            sub = subject_as_uuid(payload.get("sub"))
            async with AsyncSessionLocal() as session:
                user = await user_crud.get_by_keycloak_id(session, sub)
                if user is None and payload.get("email"):
                    user = await user_crud.get_by_email(session, str(payload["email"]).lower())
                if user is None or not user.is_active:
                    await websocket.close(code=4401)
                    return
                is_admin = user.role == "admin"
                tenant_id = user.tenant_id
                uid = user.id
        else:
            # Production: resolve context via NetHub, then local binding
            from app.api.deps import _context_to_binding, _fetch_nethub_context, _upsert_local_binding

            ctx = await _fetch_nethub_context(token)
            binding = _context_to_binding(ctx)
            async with AsyncSessionLocal() as session:
                user = await _upsert_local_binding(session, binding)
                if not user.is_active:
                    await websocket.close(code=4401)
                    return
                is_admin = user.role == "admin"
                tenant_id = user.tenant_id
                uid = user.id
    except Exception as exc:  # noqa: BLE001
        logger.debug("ws auth failed: {}", exc)
        await websocket.close(code=4401)
        return

    await websocket.accept()
    q = await subscribe(user_id=uid, tenant_id=tenant_id, is_admin=is_admin)

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
