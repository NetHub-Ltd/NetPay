"""Expire stale provider_requested payment intents (P1-A)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.domain.payment_status import IllegalTransitionError
from app.models.payment_intent import PaymentIntent
from app.services.transitions import transition_payment_intent


async def expire_stale_intents(session: AsyncSession) -> dict:
    """
    Move provider_requested intents older than STK_TIMEOUT_SECONDS to expired.
    Late provider callbacks after expiry will not auto-succeed (processor + state machine).
    """
    seconds = float(settings.stk_timeout_seconds)
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    stmt = (
        select(PaymentIntent)
        .where(PaymentIntent.status == "provider_requested")
        .where(col(PaymentIntent.deleted_at).is_(None))
        .where(PaymentIntent.updated_at < cutoff)
        .limit(200)
    )
    result = await session.exec(stmt)
    intents = list(result.all())
    expired = 0
    for intent in intents:
        try:
            await transition_payment_intent(
                session,
                intent,
                to_status="expired",
                failure_reason=f"No provider callback within {int(seconds)}s",
            )
            expired += 1
        except IllegalTransitionError as exc:
            logger.warning("expire skip {}: {}", intent.id, exc)
    if expired:
        await session.commit()
    return {"examined": len(intents), "expired": expired, "timeout_seconds": seconds}
