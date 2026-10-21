"""Structural regression tests for the NetPay persistence contract."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, DateTime
from sqlmodel import SQLModel

from app import models  # noqa: F401 — register every table before inspecting metadata
from app.models.base import require_aware_utc, utc_now
from app.models.merchants import Merchant


def test_all_domain_tables_inherit_shared_persistence_columns() -> None:
    """Every persisted model exposes the same identity and lifecycle columns."""
    expected = {"id", "created_at", "updated_at", "deleted_at"}
    assert len(SQLModel.metadata.tables) == 17
    for table in SQLModel.metadata.tables.values():
        assert expected.issubset(set(table.columns.keys())), table.name
        assert table.columns["id"].primary_key, table.name
        for column in table.columns:
            if isinstance(column.type, DateTime):
                assert column.type.timezone is True, f"{table.name}.{column.name} must be timezone-aware"


def test_utc_clock_returns_aware_utc_datetime() -> None:
    value = utc_now()
    assert value.tzinfo is not None
    assert value.utcoffset() == datetime.now(UTC).utcoffset()
    assert require_aware_utc(value).utcoffset() == UTC.utcoffset(None)


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        require_aware_utc(datetime(2026, 1, 1))


def test_soft_delete_and_restore_update_lifecycle_fields() -> None:
    merchant = Merchant(name=f"Merchant {uuid4()}")
    assert merchant.deleted_at is None
    assert not merchant.is_deleted

    merchant.soft_delete()
    assert merchant.deleted_at is not None
    assert merchant.deleted_at.tzinfo is not None
    assert merchant.is_deleted

    merchant.restore()
    assert merchant.deleted_at is None
    assert not merchant.is_deleted


def test_payment_amount_has_database_check_constraint() -> None:
    payment_table = SQLModel.metadata.tables["payment"]
    constraints = {
        constraint.name: str(constraint.sqltext)
        for constraint in payment_table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert constraints["ck_payment_amount_positive"] == "amount_minor > 0"


def test_provider_and_reconciliation_evidence_are_registered() -> None:
    expected = {
        "providerrequest",
        "paymentverification",
        "reconciliationrun",
        "reconciliationitem",
        "webhookendpoint",
        "eventdelivery",
        "auditlog",
    }
    assert expected.issubset(SQLModel.metadata.tables.keys())
