from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(max_length=120)
    slug: Optional[str] = Field(default=None, max_length=40, pattern=r"^[a-z0-9-]+$")
    category: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    status: Literal["active", "inactive"] = "active"
    id: Optional[UUID] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    category: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    status: Optional[Literal["active", "inactive"]] = None


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    category: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    model_config = {"from_attributes": True}
