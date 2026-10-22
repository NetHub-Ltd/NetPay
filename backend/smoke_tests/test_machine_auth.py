"""Unit tests for machine secret hashing and signed access tokens."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.machine_auth import (
    decode_machine_access_token,
    hash_client_secret,
    issue_machine_access_token,
    verify_client_secret,
)


def _settings(**overrides: object) -> Settings:
    """Return isolated test settings with a non-default signing key."""
    values: dict[str, object] = {
        "secret_key": "test-signing-key-that-is-at-least-32-bytes-long",
        "machine_token_ttl_minutes": 5,
        "machine_token_audience": "netpay-test",
    }
    values.update(overrides)
    return Settings(**values)


def test_client_secret_is_hashed_and_verified() -> None:
    """Hash is one-way and verification rejects wrong secrets."""
    secret = "nms_" + "s" * 48
    encoded = hash_client_secret(secret)
    assert secret not in encoded
    assert verify_client_secret(secret, encoded)
    assert not verify_client_secret("nms_" + "x" * 48, encoded)


def test_machine_token_round_trip_contains_scoped_merchant_principal() -> None:
    """Token claims produce a typed principal bound to one merchant."""
    merchant_id = uuid4()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = issue_machine_access_token(
        client_id="nmc_test-client",
        merchant_id=merchant_id,
        scopes=["payments:write", "payments:read"],
        settings=_settings(),
        now=now,
    )
    principal = decode_machine_access_token(
        token,
        settings=_settings(),
        now=now + timedelta(seconds=1),
    )
    assert principal.client_id == "nmc_test-client"
    assert principal.merchant_id == merchant_id
    assert principal.scopes == frozenset({"payments:write", "payments:read"})


def test_machine_token_rejects_expired_token() -> None:
    """Expired machine tokens fail closed."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = issue_machine_access_token(
        client_id="nmc_test-client",
        merchant_id=uuid4(),
        scopes=["payments:read"],
        settings=_settings(),
        now=now,
    )
    with pytest.raises(ValueError):
        decode_machine_access_token(token, settings=_settings(), now=now + timedelta(minutes=6))


def test_machine_token_rejects_wrong_audience() -> None:
    """Tokens minted for another audience are not accepted."""
    token = issue_machine_access_token(
        client_id="nmc_test-client",
        merchant_id=uuid4(),
        scopes=["payments:read"],
        settings=_settings(),
    )
    with pytest.raises(ValueError):
        decode_machine_access_token(token, settings=_settings(machine_token_audience="another-service"))


def test_machine_token_rejects_tampering() -> None:
    """Changing the token payload invalidates its signature."""
    token = issue_machine_access_token(
        client_id="nmc_test-client",
        merchant_id=uuid4(),
        scopes=["payments:read"],
        settings=_settings(),
    )
    pieces = token.split(".")
    pieces[1] = ("A" if pieces[1][0] != "A" else "B") + pieces[1][1:]
    with pytest.raises(ValueError):
        decode_machine_access_token(".".join(pieces), settings=_settings())
