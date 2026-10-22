"""Regression tests for configuration and the complete SQLModel schema."""
from datetime import UTC

import pytest
from sqlalchemy import DateTime
from sqlalchemy.engine import make_url
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


def test_connection_urls_are_built_from_split_secret_settings() -> None:
    """Both driver URLs preserve credentials without leaking them in settings repr."""
    reserved_password = "p" + "@ss:/%" + " word"
    settings = Settings(
        db_host="db.example.test",
        db_port=5432,
        db_name="netpay",
        db_user="private-user",
        db_password=reserved_password,
        db_ssl_mode="require",
    )
    async_url = make_url(settings.async_database_url())
    sync_url = make_url(settings.alembic_database_url())

    assert async_url.drivername == "postgresql+asyncpg"
    assert sync_url.drivername == "postgresql+psycopg"
    assert async_url.username == "private-user"
    assert sync_url.username == "private-user"
    for url in (async_url, sync_url):
        assert url.password == reserved_password
        assert url.host == "db.example.test"
        assert url.database == "netpay"
    assert async_url.query["ssl"] == "require"
    assert sync_url.query["sslmode"] == "require"
    assert reserved_password not in repr(settings)
    assert "private-user" not in repr(settings)


def test_database_configuration_validates_pool_and_port() -> None:
    """Invalid database port or pool values fail validation."""
    with pytest.raises(ValueError):
        Settings(db_port=70000)
    with pytest.raises(ValueError):
        Settings(db_pool_size=0)
    with pytest.raises(ValueError):
        Settings(db_max_overflow=-1)


def test_legacy_database_url_can_bridge_existing_deployments() -> None:
    """An existing DATABASE_URL remains usable during the environment migration."""
    settings = Settings(
        database_url="postgresql+asyncpg://legacy-user:legacy-pass@db.internal:5433/gateway?sslmode=require"
    )
    url = make_url(settings.async_database_url())
    assert url.host == "db.internal"
    assert url.port == 5433
    assert url.database == "gateway"
    assert url.username == "legacy-user"
    assert url.password == "legacy-pass"
    assert url.query["ssl"] == "require"


def test_conservative_pool_defaults() -> None:
    """Default pool keeps only one persistent connection and no overflow."""
    settings = Settings()
    assert settings.db_pool_size == 1
    assert settings.db_max_overflow == 0


def test_all_sixteen_domain_tables_are_registered() -> None:
    """Every intended domain table is registered exactly once for Alembic."""
    assert set(SQLModel.metadata.tables) == EXPECTED_TABLES
    assert len(SQLModel.metadata.tables) == 16


def test_lifecycle_columns_are_timezone_aware() -> None:
    """Every model uses timezone-aware lifecycle timestamps."""
    for table in SQLModel.metadata.tables.values():
        for name in ("created_at", "updated_at", "deleted_at"):
            assert name in table.c, f"{table.name}.{name} missing"
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
