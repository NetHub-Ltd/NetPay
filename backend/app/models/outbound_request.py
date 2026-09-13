from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.models.base import BaseMixin


class OutboundRequest(BaseMixin, table=True):
    """Audit log of every HTTP call NetPay makes to external providers (e.g. Daraja)."""

    __tablename__ = "outbound_requests"

    tenant_id: Optional[UUID] = Field(default=None, index=True)
    integration_id: Optional[UUID] = Field(default=None, index=True)
    provider: str = Field(default="mpesa", max_length=32, index=True)
    operation: str = Field(max_length=64, index=True)  # oauth, stk_push, c2b_register_urls, …
    method: str = Field(max_length=10)
    url: str = Field(max_length=1024)
    request_body: Optional[str] = Field(default=None)
    response_status: Optional[int] = Field(default=None, index=True)
    response_body: Optional[str] = Field(default=None)
    success: bool = Field(default=False, index=True)
    error_message: Optional[str] = Field(default=None, max_length=1024)
    duration_ms: Optional[int] = Field(default=None)
