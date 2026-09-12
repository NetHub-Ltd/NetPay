"""Central PaymentIntent status transitions."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.payment_intent import payment_intent_crud
from app.domain.payment_status import IllegalTransitionError, assert_can_transition, is_terminal
from app.models.payment_intent import PaymentIntent


async def transition_payment_intent(
    session: AsyncSession,
    intent: PaymentIntent,
    *,
    to_status: str,
    provider_checkout_id: Optional[str] = None,
    provider_merchant_id: Optional[str] = None,
    provider_transaction_id: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> PaymentIntent:
    """
    Apply a legal status transition and optional provider field updates.

    Raises IllegalTransitionError if the transition is not allowed.
    """
    assert_can_transition(intent.status, to_status)
    update: dict[str, Any] = {"status": to_status}
    if provider_checkout_id is not None:
        update["provider_checkout_id"] = provider_checkout_id
    if provider_merchant_id is not None:
        update["provider_merchant_id"] = provider_merchant_id
    if provider_transaction_id is not None:
        update["provider_transaction_id"] = provider_transaction_id
    if failure_reason is not None:
        update["failure_reason"] = failure_reason[:512]
    return await payment_intent_crud.update(session, db_obj=intent, obj_in=update)


async def try_transition_payment_intent(
    session: AsyncSession,
    intent: PaymentIntent,
    *,
    to_status: str,
    **kwargs: Any,
) -> tuple[PaymentIntent, bool]:
    """
    Transition if legal; if already terminal and target equals current, no-op success.
    Returns (intent, changed).
    """
    if intent.status == to_status:
        return intent, False
    if is_terminal(intent.status):
        raise IllegalTransitionError(intent.status, to_status)
    updated = await transition_payment_intent(session, intent, to_status=to_status, **kwargs)
    return updated, True
