from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session
from app.crud.event import event_crud
from app.models.event import GatewayEvent
from app.models.user import User
from app.schemas.event import EventOut
from app.services.webhooks import fanout_webhooks

router = APIRouter(prefix="/v1/events", tags=["events"])


@router.get("", response_model=list[EventOut])
async def list_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[GatewayEvent]:
    return list(
        await event_crud.list_for_user(
            session,
            tenant_id=user.tenant_id,
            is_admin=user.role == "admin",
        )
    )


@router.post("/{event_id}/replay")
async def replay_event(
    event_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    ev = await event_crud.get(session, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if not can_access_tenant(user, ev.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not ev.is_replayable:
        raise HTTPException(status_code=400, detail="Event is not replayable")
    payload = {
        "event": "nethub.event.replay",
        "original_action": ev.action,
        "message": ev.message,
        "payment_intent_id": str(ev.payment_intent_id) if ev.payment_intent_id else None,
    }
    if ev.payment_intent_id:
        await fanout_webhooks(session, ev.tenant_id, ev.payment_intent_id, payload)
        await session.commit()
    return {"ok": True, "replayed": str(ev.id)}
