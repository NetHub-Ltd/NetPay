from __future__ import annotations

from decimal import Decimal
from typing import Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.payment_intent import PaymentIntent


class PaymentIntentCreateIn(BaseModel):
    tenant_id: UUID
    integration_id: UUID
    created_by: Optional[UUID] = None
    intent_type: str = "collection"
    status: str = "created"
    amount: Decimal
    amount_minor: int
    currency: str = "KES"
    phone: str
    account_reference: Optional[str] = None
    description: Optional[str] = None
    context_json: Optional[str] = None
    provider: str = "mpesa"
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    idempotency_key: Optional[str] = None


class PaymentIntentUpdate(BaseModel):
    status: Optional[str] = None
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    amount_minor: Optional[int] = None
    amount: Optional[Decimal] = None


class PaymentIntentCRUD(BaseCRUD[PaymentIntent, PaymentIntentCreateIn, PaymentIntentUpdate]):
    def __init__(self, model: Type[PaymentIntent] = PaymentIntent):
        super().__init__(model)

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[UUID],
        is_admin: bool,
        limit: int = 80,
    ) -> Sequence[PaymentIntent]:
        where = []
        if not is_admin:
            if not tenant_id:
                return []
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

    async def get_by_checkout_id(
        self, db: AsyncSession, checkout_id: str
    ) -> Optional[PaymentIntent]:
        rows = await self.get_by_attributes(
            db, filters={"provider_checkout_id": checkout_id}, limit=1
        )
        return rows[0] if rows else None

    async def get_by_idempotency(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        idempotency_key: str,
    ) -> Optional[PaymentIntent]:
        rows = await self.get_by_attributes(
            db,
            filters={"tenant_id": tenant_id, "idempotency_key": idempotency_key},
            limit=1,
        )
        return rows[0] if rows else None

    async def find_open_by_account_reference(
        self,
        db: AsyncSession,
        *,
        integration_id: UUID,
        account_reference: str,
    ) -> Optional[PaymentIntent]:
        """Most recent non-terminal intent for this integration + account reference."""
        from sqlmodel import select
        terminal = ("succeeded", "failed", "expired")
        stmt = (
            select(PaymentIntent)
            .where(PaymentIntent.integration_id == integration_id)
            .where(PaymentIntent.account_reference == account_reference)
            .where(col(PaymentIntent.deleted_at).is_(None))
            .where(~col(PaymentIntent.status).in_(terminal))
            .order_by(col(PaymentIntent.created_at).desc())
            .limit(1)
        )
        result = await db.exec(stmt)
        return result.first()


payment_intent_crud = PaymentIntentCRUD(PaymentIntent)
