from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class Tenant(BaseMixin, table=True):
    __tablename__ = "tenants"
    name: str = Field(max_length=120)
    slug: str = Field(index=True, unique=True, max_length=40)
    status: str = Field(default="active", max_length=32)  # active | inactive
    category: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    # NetHub principal id — no local users FK
    created_by: UUID = Field(index=True)
