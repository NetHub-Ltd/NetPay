"""Ledger posting helpers — append-only."""
from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.crud.ledger import ledger_entry_crud
from app.models.payment_intent import PaymentIntent

ENTRY_COLLECTION_CREDIT = "collection_credit"


async def post_collection_credit(
    session: AsyncSession,
    intent: PaymentIntent,
) -> bool:
    """
    Append a collection_credit for a succeeded intent if none exists.
    Returns True if a new row was written.
    Unique (payment_intent_id, entry_type) is the hard guarantee against doubles.
    """
    if intent.status != "succeeded":
        return False
    existing = await ledger_entry_crud.count_for_intent_type(
        session,
        payment_intent_id=intent.id,
        entry_type=ENTRY_COLLECTION_CREDIT,
    )
    if existing:
        logger.info("Ledger collection_credit already present for intent={}", intent.id)
        return False
    await ledger_entry_crud.create(
        session,
        obj_in={
            "tenant_id": intent.tenant_id,
            "payment_intent_id": intent.id,
            "entry_type": ENTRY_COLLECTION_CREDIT,
            "amount_minor": intent.amount_minor,
            "currency": intent.currency,
            "provider_ref": intent.provider_transaction_id or intent.provider_checkout_id,
            "note": "STK collection settled",
        },
    )
    return True
