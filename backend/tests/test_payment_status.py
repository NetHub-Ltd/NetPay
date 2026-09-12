"""Unit tests for payment state machine (P0)."""
from __future__ import annotations

import pytest

from app.domain.payment_status import (
    IllegalTransitionError,
    PaymentStatus,
    assert_can_transition,
    is_terminal,
    major_units_from_minor,
)


def test_allowed_happy_path():
    assert_can_transition("created", "provider_requested")
    assert_can_transition("provider_requested", "succeeded")


def test_terminal_no_regression():
    with pytest.raises(IllegalTransitionError):
        assert_can_transition("succeeded", "failed")
    with pytest.raises(IllegalTransitionError):
        assert_can_transition("failed", "succeeded")
    with pytest.raises(IllegalTransitionError):
        assert_can_transition("succeeded", "provider_requested")


def test_is_terminal():
    assert is_terminal(PaymentStatus.SUCCEEDED)
    assert is_terminal("failed")
    assert not is_terminal("created")
    assert not is_terminal("provider_requested")


def test_major_units_kes():
    assert major_units_from_minor(100) == 1
    assert major_units_from_minor(2500) == 25
    with pytest.raises(ValueError):
        major_units_from_minor(50)
    with pytest.raises(ValueError):
        major_units_from_minor(0)
