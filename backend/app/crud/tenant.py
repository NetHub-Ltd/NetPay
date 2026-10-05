from __future__ import annotations

from typing import Optional, Sequence, Type
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantCRUD(BaseCRUD[Tenant, TenantCreate, TenantUpdate]):
    def __init__(self, model: Type[Tenant] = Tenant):
        super().__init__(model)

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Tenant]:
        rows = await self.get_by_attributes(db, filters={"slug": slug}, limit=1)
        return rows[0] if rows else None

    async def list_all(self, db: AsyncSession, *, skip: int = 0, limit: int = 200) -> Sequence[Tenant]:
        items, _ = await self.get_multi_paginated(
            db, skip=skip, limit=limit, sort_by="created_at", sort_order="desc"
        )
        return items

    async def create_tenant(
        self,
        db: AsyncSession,
        *,
        name: str,
        slug: str,
        created_by: UUID,
        id: Optional[UUID] = None,
        category: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        status: str = "active",
    ) -> Tenant:
        payload = {
            "name": name,
            "slug": slug,
            "created_by": created_by,
            "status": status,
            "category": category,
            "email": email,
            "phone_number": phone_number,
        }
        if id is not None:
            payload["id"] = id
        return await self.create(db, obj_in=payload)


tenant_crud = TenantCRUD(Tenant)
