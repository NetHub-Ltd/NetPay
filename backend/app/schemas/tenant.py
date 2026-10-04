from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(max_length=120)
    slug: Optional[str] = Field(default=None, max_length=40, pattern=r"^[a-z0-9-]+$")
    # Optional: force id to match NetHub tenant_id (parent org)
    id: Optional[UUID] = None


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    model_config = {"from_attributes": True}
