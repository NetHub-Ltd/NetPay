"""Merchant ownership and machine-to-machine credentials."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field

from app.models.base import BaseMixin


class Merchant(BaseMixin, table=True):
    """Tenant root for payments, integrations, clients, and event delivery."""

    name: str = Field(max_length=120, index=True)
    slug: str = Field(default_factory=lambda: f"merchant-{uuid4().hex}", max_length=100, unique=True, index=True)
    status: str = Field(default="active", max_length=24, index=True)
    default_currency: str = Field(default="KES", min_length=3, max_length=3)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=20)
    # Extensible non-critical attributes only; business invariants remain columns.
    attributes: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class M2MClient(BaseMixin, table=True):
    """Machine credential owned by exactly one merchant.

    Only a one-way secret hash is stored; plaintext is shown at issuance time
    and cannot be recovered from this record.
    """

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    client_id: str = Field(max_length=80, unique=True, index=True)
    secret_hash: str = Field(max_length=255)
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: str = Field(default="active", max_length=24, index=True)
    last_used_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
