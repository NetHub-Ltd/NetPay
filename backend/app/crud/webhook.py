from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.webhook import Webhook, WebhookDelivery


class WebhookCreateIn(BaseModel):
    tenant_id: UUID
    url: str
    secret: str
    last_live_at: Optional[datetime] = None


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    secret: Optional[str] = None
    last_live_at: Optional[datetime] = None


class WebhookDeliveryCreateIn(BaseModel):
    webhook_id: UUID
    payment_intent_id: Optional[UUID] = None
    status_code: Optional[int] = None
    ok: bool = False
    error: Optional[str] = None


class WebhookDeliveryUpdate(BaseModel):
    status_code: Optional[int] = None
    ok: Optional[bool] = None
    error: Optional[str] = None


class WebhookCRUD(BaseCRUD[Webhook, WebhookCreateIn, WebhookUpdate]):
    def __init__(self, model: Type[Webhook] = Webhook):
        super().__init__(model)

    async def list_by_tenant(
        self, db: AsyncSession, tenant_id: UUID, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Webhook]:
        items, _ = await self.get_multi_paginated(
            db,
            skip=skip,
            limit=limit,
            where_clauses=[col(self.model.tenant_id) == tenant_id],
            sort_by="created_at",
            sort_order="asc",
        )
        return items

    async def count_by_tenant(self, db: AsyncSession, tenant_id: UUID) -> int:
        return await self.count(db, where_clauses=[col(self.model.tenant_id) == tenant_id])


class WebhookDeliveryCRUD(BaseCRUD[WebhookDelivery, WebhookDeliveryCreateIn, WebhookDeliveryUpdate]):
    def __init__(self, model: Type[WebhookDelivery] = WebhookDelivery):
        super().__init__(model)


webhook_crud = WebhookCRUD(Webhook)
webhook_delivery_crud = WebhookDeliveryCRUD(WebhookDelivery)
