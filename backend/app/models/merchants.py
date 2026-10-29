"""Merchant ownership and machine-to-machine credentials."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, JSON, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class Merchant(BaseMixin, table=True):
    """Tenant root for integrations, payments, clients, and event delivery."""

    __tablename__ = "merchant"
    __table_args__ = (UniqueConstraint("slug", name="uq_merchant_slug"),)

    name: str = Field(max_length=160)
    slug: str = Field(max_length=100)
    default_currency: str = Field(default="KES", min_length=3, max_length=3)
    status: str = Field(default="active", max_length=24)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=20)
    attributes: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class M2MClient(BaseMixin, table=True):
    """A merchant-owned machine credential; only a one-way secret hash is stored."""

    __tablename__ = "m2mclient"
    __table_args__ = (UniqueConstraint("client_id", name="uq_m2mclient_client_id"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    client_id: str = Field(max_length=80)
    secret_hash: str = Field(max_length=255)
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: str = Field(default="active", max_length=24, index=True)
    last_used_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    expires_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), index=True)
    revoked_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
