"""Regression tests for configuration and the complete SQLModel schema."""

from datetime import UTC
import pytest
from sqlalchemy import DateTime
from sqlmodel import SQLModel

from app.core.config import Settings
from app.models import *  # noqa: F403


EXPECTED_TABLES = {
    "merchant",
    "providerintegration",
    "m2mclient",
    "payment",
    "paymentattempt",
    "idempotencyrecord",
    "paymentverification",
    "providerrequest",
    "providercallback",
    "reconciliationrun",
    "reconciliationitem",
    "eventoutbox",
    "webhookendpoint",
    "eventdelivery",
    "eventdeliveryattempt",
    "auditevent",
}


def test_connection_strings_are_secret_wrapped() -> None:
    """Settings repr must not reveal database or Redis credentials."""
    settings = Settings(
        database_url="postgresql+asyncpg://private:secret@localhost/netpay",
        redis_url="redis://private:secret@localhost/0",
    )
    assert "secret" not in repr(settings)
    assert "private" not in repr(settings)
    assert settings.alembic_database_url().startswith("postgresql+psycopg://")


def test_database_url_requires_async_postgresql() -> None:
    """Unsupported database connection schemes fail validation."""
    with pytest.raises(ValueError):
        Settings(database_url="sqlite:///./test.db")


def test_all_sixteen_domain_tables_are_registered() -> None:
    """Every intended domain table is registered exactly once for Alembic."""
    assert set(SQLModel.metadata.tables) == EXPECTED_TABLES
    assert len(SQLModel.metadata.tables) == 16


def test_lifecycle_columns_are_timezone_aware() -> None:
    """Every model uses timezone-aware lifecycle timestamps."""
    for table in SQLModel.metadata.tables.values():
        for name in ("created_at", "updated_at", "deleted_at"):
            assert name in table.c, f"{table.name}.{name} missing"
            if name != "deleted_at":
                assert isinstance(table.c[name].type, DateTime)
                assert table.c[name].type.timezone is True
            else:
                assert isinstance(table.c[name].type, DateTime)
                assert table.c[name].type.timezone is True


def test_money_and_integrity_invariants_are_database_enforced() -> None:
    """Payment amounts and reconciliation windows have explicit constraints."""
    payment_checks = {constraint.name for constraint in SQLModel.metadata.tables["payment"].constraints}
    run_checks = {constraint.name for constraint in SQLModel.metadata.tables["reconciliationrun"].constraints}
    assert "ck_payment_amount_positive" in payment_checks
    assert "ck_reconciliation_window_order" in run_checks


def test_clock_is_utc_aware() -> None:
    """The timestamp factory returns an aware UTC datetime."""
    from app.models.base import utc_now

    assert utc_now().utcoffset() == UTC.utcoffset(None)
