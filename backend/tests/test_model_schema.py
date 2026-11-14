"""Check key constraints and indexes in the registered domain schema."""

from app import models  # noqa: F401 - ensure every model is registered
from sqlmodel import SQLModel


def test_financial_records_have_expected_uniqueness_constraints() -> None:
    """Database constraints protect merchant references and callback deduplication."""
    tables = SQLModel.metadata.tables
    payment_constraints = {c.name for c in tables["payment"].constraints}
    callback_constraints = {c.name for c in tables["providercallback"].constraints}
    idempotency_constraints = {c.name for c in tables["idempotencyrecord"].constraints}

    assert "uq_payment_merchant_reference" in payment_constraints
    assert "uq_callback_integration_fingerprint" in callback_constraints
    assert "uq_idempotency_merchant_key" in idempotency_constraints


def test_no_legacy_compatibility_destination_table_is_registered() -> None:
    """Only the normalized webhook endpoint/delivery design is registered."""
    assert "eventdestination" not in SQLModel.metadata.tables
    assert "webhookendpoint" in SQLModel.metadata.tables
    assert "eventdelivery" in SQLModel.metadata.tables
    assert "eventdeliveryattempt" in SQLModel.metadata.tables
