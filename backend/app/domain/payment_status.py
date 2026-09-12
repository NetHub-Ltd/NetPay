"""PaymentIntent status machine — P0 financial integrity."""
from __future__ import annotations

from enum import StrEnum


class PaymentStatus(StrEnum):
    CREATED = "created"
    PROVIDER_REQUESTED = "provider_requested"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


TERMINAL = frozenset(
    {
        PaymentStatus.SUCCEEDED,
        PaymentStatus.FAILED,
        PaymentStatus.EXPIRED,
    }
)

# from_status -> allowed to_status
ALLOWED_TRANSITIONS: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    PaymentStatus.CREATED: frozenset(
        {PaymentStatus.PROVIDER_REQUESTED, PaymentStatus.FAILED}
    ),
    PaymentStatus.PROVIDER_REQUESTED: frozenset(
        {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED, PaymentStatus.EXPIRED}
    ),
    PaymentStatus.SUCCEEDED: frozenset(),
    PaymentStatus.FAILED: frozenset(),
    PaymentStatus.EXPIRED: frozenset(),
}


class IllegalTransitionError(ValueError):
    """Raised when a status change is not allowed by the state machine."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Illegal payment transition: {current!r} → {target!r}")


def parse_status(value: str) -> PaymentStatus:
    try:
        return PaymentStatus(value)
    except ValueError as exc:
        raise IllegalTransitionError(value, value) from exc


def is_terminal(status: str | PaymentStatus) -> bool:
    try:
        s = status if isinstance(status, PaymentStatus) else PaymentStatus(status)
    except ValueError:
        return False
    return s in TERMINAL


def assert_can_transition(current: str, target: str) -> None:
    cur = parse_status(current)
    tgt = parse_status(target)
    if tgt not in ALLOWED_TRANSITIONS.get(cur, frozenset()):
        raise IllegalTransitionError(current, target)


def major_units_from_minor(amount_minor: int, *, currency: str = "KES") -> int:
    """Convert minor units to whole major units for providers that require integers (Daraja STK)."""
    if amount_minor <= 0:
        raise ValueError("amount_minor must be positive")
    # KES: 100 minor = 1 KES; Daraja expects whole shillings
    if currency.upper() == "KES":
        major = amount_minor // 100
        if major < 1:
            raise ValueError("amount_minor must be at least 100 (1 KES)")
        return major
    major = amount_minor // 100
    if major < 1:
        raise ValueError("amount_minor too small for provider major units")
    return major
