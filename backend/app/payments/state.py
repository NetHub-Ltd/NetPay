"""Payment state transitions shared by initiation and callbacks."""

from datetime import datetime, timezone
from typing import Literal

from app.models import Payment

PaymentStatus = Literal["pending", "succeeded", "failed", "cancelled", "expired", "unknown"]
_TERMINAL = {"succeeded", "failed", "cancelled"}
_ALLOWED: dict[str, set[str]] = {
    "pending": {"succeeded", "failed", "cancelled", "expired", "unknown"},
    "unknown": {"succeeded", "failed", "cancelled", "expired"},
    "expired": {"succeeded", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


def apply_status(payment: Payment, new_status: PaymentStatus) -> bool:
    """Apply a legal transition and return whether state changed.

    Terminal states never regress on conflicting or late callbacks. Late evidence
    may resolve unknown/expired payments, but conflicting terminal evidence is
    retained in callback history for manual reconciliation.
    """
    current = payment.status
    if current == new_status:
        return False
    if new_status not in _ALLOWED.get(current, set()):
        return False
    payment.status = new_status
    payment.updated_at = datetime.now(timezone.utc)
    if new_status in _TERMINAL:
        payment.completed_at = datetime.now(timezone.utc)
    return True
