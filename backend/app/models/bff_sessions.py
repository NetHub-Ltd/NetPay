"""Opaque server-side application sessions used by the Next.js BFF."""
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Text
from sqlmodel import Field, SQLModel


class BFFSession(SQLModel, table=True):
    """Hashed session handle and encrypted upstream OIDC tokens.

    The browser receives only the random session handle in an HttpOnly cookie.
    Access and refresh tokens are encrypted with a dedicated BFF key at rest.
    """

    __tablename__ = "bffsession"
    __table_args__ = (
        Index("ix_bffsession_expires_at", "expires_at"),
        Index("ix_bffsession_access_expires_at", "access_expires_at"),
    )

    session_id_hash: str = Field(primary_key=True, max_length=64)
    access_token_ciphertext: str = Field(sa_type=Text, nullable=False)
    refresh_token_ciphertext: str | None = Field(default=None, sa_type=Text)
    access_expires_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    version: int = Field(default=1, nullable=False)
    expires_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True), nullable=False)
    revoked_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
