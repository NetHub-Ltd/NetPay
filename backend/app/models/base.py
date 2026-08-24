from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import DateTime, text
from sqlmodel import Field, SQLModel

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class BaseMixin(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "nullable": False},
    )
    deleted_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
