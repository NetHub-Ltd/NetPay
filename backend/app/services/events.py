from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.event import event_crud
from app.models.event import GatewayEvent


async def record_event(
    session: AsyncSession,
    *,
    category: str,
    action: str,
    message: str,
    tenant_id: Optional[UUID] = None,
    integration_id: Optional[UUID] = None,
    payment_intent_id: Optional[UUID] = None,
    payload: Optional[dict[str, Any]] = None,
    is_replayable: bool = False,
) -> GatewayEvent:
    ev = await event_crud.create(
        session,
        obj_in={
            "tenant_id": tenant_id,
            "integration_id": integration_id,
            "payment_intent_id": payment_intent_id,
            "category": category,
            "action": action,
            "message": message[:512],
            "payload_json": json.dumps(payload) if payload else None,
            "is_replayable": is_replayable,
        },
    )
    await session.commit()
    await session.refresh(ev)
    return ev
