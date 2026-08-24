from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, Field

class TenantCreate(BaseModel):
    name: str = Field(max_length=120)
    slug: str = Field(max_length=40, pattern=r"^[a-z0-9-]+$")

class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    model_config = {"from_attributes": True}

class AssignUserRequest(BaseModel):
    email: str
    password: str
    tenant_id: UUID
    display_name: str | None = None
