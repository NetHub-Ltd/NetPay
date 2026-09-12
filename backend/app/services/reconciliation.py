"""Reconciliation scan — surface mismatches for operators (P1-B skeleton)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.crud.reconciliation import reconciliation_crud
from app.models.inbound_event import InboundEvent
from app.models.ledger import LedgerEntry
from app.models.payment_intent import PaymentIntent


async def run_reconciliation_scan(session: AsyncSession) -> dict:
    """
    Lightweight internal consistency scan (not a full Daraja statement pull).

    Detects:
    - succeeded intents without a collection_credit ledger row
    - provider_requested older than 2x STK timeout still open (stale_pending)
    - inbound events in dead status without resolution note (surface count)
    """
    created = 0
    notes: list[str] = []

    # 1) Succeeded without ledger credit
    stmt = (
        select(PaymentIntent)
        .where(PaymentIntent.status == "succeeded")
        .where(col(PaymentIntent.deleted_at).is_(None))
        .limit(500)
    )
    intents = list((await session.exec(stmt)).all())
    for intent in intents:
        led = await session.exec(
            select(LedgerEntry).where(
                LedgerEntry.payment_intent_id == intent.id,
                LedgerEntry.entry_type == "collection_credit",
            )
        )
        if led.first():
            continue
        existing = await reconciliation_crud.find_open_for_intent(
            session, payment_intent_id=intent.id, kind="unmatched_netpay"
        )
        if existing:
            continue
        await reconciliation_crud.create(
            session,
            obj_in={
                "tenant_id": intent.tenant_id,
                "payment_intent_id": intent.id,
                "kind": "unmatched_netpay",
                "status": "open",
                "provider_ref": intent.provider_transaction_id or intent.provider_checkout_id,
                "message": "Succeeded payment has no collection_credit ledger row",
            },
        )
        created += 1

    # 2) Very stale provider_requested (2x timeout) — may need ops attention beyond expire job
    seconds = float(settings.stk_timeout_seconds) * 2
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    stmt2 = (
        select(PaymentIntent)
        .where(PaymentIntent.status == "provider_requested")
        .where(col(PaymentIntent.deleted_at).is_(None))
        .where(PaymentIntent.updated_at < cutoff)
        .limit(200)
    )
    for intent in list((await session.exec(stmt2)).all()):
        existing = await reconciliation_crud.find_open_for_intent(
            session, payment_intent_id=intent.id, kind="stale_pending"
        )
        if existing:
            continue
        await reconciliation_crud.create(
            session,
            obj_in={
                "tenant_id": intent.tenant_id,
                "payment_intent_id": intent.id,
                "kind": "stale_pending",
                "status": "open",
                "provider_ref": intent.provider_checkout_id,
                "message": f"Still waiting on M-Pesa after {int(seconds)}s — run expire-stale or investigate",
            },
        )
        created += 1

    dead_count = 0
    dead_stmt = select(InboundEvent).where(InboundEvent.status == "dead").limit(500)
    dead_count = len(list((await session.exec(dead_stmt)).all()))
    if dead_count:
        notes.append(f"{dead_count} inbound event(s) in dead-letter")

    await session.commit()
    return {"exceptions_created": created, "notes": notes, "dead_inbound_events": dead_count}
