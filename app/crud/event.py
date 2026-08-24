from __future__ import annotations

from typing import Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.event import GatewayEvent


class GatewayEventCreateIn(BaseModel):
    tenant_id: Optional[UUID] = None
    integration_id: Optional[UUID] = None
    payment_intent_id: Optional[UUID] = None
    category: str
    action: str
    message: str
    payload_json: Optional[str] = None
    is_replayable: bool = False


class GatewayEventUpdate(BaseModel):
    is_replayable: Optional[bool] = None
    message: Optional[str] = None


class EventCRUD(BaseCRUD[GatewayEvent, GatewayEventCreateIn, GatewayEventUpdate]):
    def __init__(self, model: Type[GatewayEvent] = GatewayEvent):
        super().__init__(model)

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[UUID],
        is_admin: bool,
        limit: int = 100,
    ) -> Sequence[GatewayEvent]:
        where = []
        if not is_admin and tenant_id:
            where.append(col(self.model.tenant_id) == tenant_id)
        items, _ = await self.get_multi_paginated(
            db,
            skip=0,
            limit=limit,
            where_clauses=where or None,
            sort_by="created_at",
            sort_order="desc",
        )
        return items


event_crud = EventCRUD(GatewayEvent)
