"""Configuration and schema invariants for the database phase."""
from datetime import UTC
import pytest
from sqlalchemy import DateTime
from sqlmodel import SQLModel
from app.core.config import Settings
from app.models import *  # noqa: F403

def test_connection_strings_are_secret_wrapped() -> None:
    """Settings repr does not reveal connection credentials."""
    settings = Settings(database_url="postgresql+asyncpg://private:secret@localhost/netpay", redis_url="redis://private:secret@localhost/0")
    assert "secret" not in repr(settings)
    assert "private" not in repr(settings)
    assert settings.alembic_database_url().startswith("postgresql+psycopg://")

def test_database_url_requires_async_postgresql() -> None:
    """Unsupported connection schemes fail validation."""
    with pytest.raises(ValueError):
        Settings(database_url="sqlite:///./test.db")

def test_core_tables_are_registered() -> None:
    """The fresh schema registers durable payment and operational records."""
    assert {"merchant", "providerintegration", "payment", "paymentattempt", "idempotencyrecord", "providercallback", "eventoutbox", "auditevent"}.issubset(SQLModel.metadata.tables)

def test_lifecycle_columns_are_timezone_aware() -> None:
    """Shared timestamps map to timezone-aware database columns."""
    for table in SQLModel.metadata.tables.values():
        for name in ("created_at", "updated_at", "deleted_at"):
            if name in table.c:
                assert isinstance(table.c[name].type, DateTime)
                assert table.c[name].type.timezone is True

def test_clock_is_utc_aware() -> None:
    """The UTC timestamp factory returns an aware datetime."""
    from app.models.domain import utc_now
    assert utc_now().utcoffset() == UTC.utcoffset(None)
