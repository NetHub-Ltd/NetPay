"""Merchant ownership and machine-to-machine credentials."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Merchant(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120, index=True)
    status: str = Field(default="active", max_length=24, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class M2MClient(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    client_id: str = Field(max_length=80, unique=True, index=True)
    secret_hash: str = Field(max_length=255)
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: str = Field(default="active", max_length=24, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    last_used_at: datetime | None = Field(default=None)
