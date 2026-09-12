"""Durable inbound provider envelopes (P1-A)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, Integer, Text, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class InboundEvent(BaseMixin, table=True):
    __tablename__ = "inbound_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_inbound_events_event_id"),)

    event_id: str = Field(max_length=128, index=True)
    provider: str = Field(default="mpesa", max_length=32)
    event_type: str = Field(max_length=64)
    integration_public_id: Optional[str] = Field(default=None, max_length=64)
    payload_json: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(default="received", max_length=32, index=True)
    # received | processing | processed | failed | dead
    attempts: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    last_error: Optional[str] = Field(default=None, max_length=512)
    result_json: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
