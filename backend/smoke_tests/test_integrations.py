"""Route-level tests for merchant-scoped Daraja integration onboarding."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from pydantic import SecretStr

from app.api.integrations import (
    IntegrationCreateRequest,
    create_integration,
    get_integration,
    list_integrations,
)
from app.core.config import Settings
from app.core.credentials import decrypt_credential
from app.core.machine_auth import MachinePrincipal
from app.models.integrations import DarajaIntegration
from app.providers.daraja import DarajaCredentialsRejected, DarajaUnavailable


def _settings(key: str | None = None) -> Settings:
    """Return isolated onboarding settings with a stable public callback origin."""
    return Settings(
        environment="test",
        secret_key="test-signing-key-that-is-at-least-32-bytes-long",
        credential_encryption_key=key,
        public_api_base_url="https://pay.example.test",
        daraja_timeout_seconds=3,
    )


def _result(value: object) -> MagicMock:
    """Build the minimal SQLModel result interface used by the routes."""
    result = MagicMock()
    result.first.return_value = value
    result.all.return_value = value if isinstance(value, list) else []
    return result


def _principal(merchant_id=None) -> MachinePrincipal:
    """Create a typed principal scoped to one merchant."""
    return MachinePrincipal(
        client_id="nmc_test-client",
        merchant_id=merchant_id or uuid4(),
        scopes=frozenset({"integrations:read", "integrations:write"}),
    )


def _body() -> IntegrationCreateRequest:
    """Return credentials that must never be included in a response."""
    return IntegrationCreateRequest(
        environment="sandbox",
        shortcode="174379",
        product_type="paybill",
        consumer_key="consumer-key-private",
        consumer_secret="consumer-secret-private",
        passkey="passkey-private",
    )


@pytest.mark.asyncio
async def test_create_integration_encrypts_credentials_and_generates_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid provider credentials create an active tenant-owned integration."""
    key = Fernet.generate_key().decode("ascii")
    settings = _settings(key)
    monkeypatch.setattr("app.api.integrations.get_settings", lambda: settings)

    async def validate(**kwargs: object) -> None:
        assert kwargs["environment"] == "sandbox"
        assert kwargs["consumer_key"] == "consumer-key-private"
        assert kwargs["consumer_secret"] == "consumer-secret-private"
        assert kwargs["timeout_seconds"] == 3

    monkeypatch.setattr("app.api.integrations.validate_daraja_credentials", validate)
    principal = _principal()
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(None))
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    response = await create_integration(_body(), principal, session)

    stored = next(call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], DarajaIntegration))
    assert stored.merchant_id == principal.merchant_id
    assert stored.status == "active"
    assert stored.credential_status == "valid"
    assert stored.consumer_key_ciphertext != b"consumer-key-private"
    assert decrypt_credential(stored.consumer_key_ciphertext, key=key) == "consumer-key-private"
    assert decrypt_credential(stored.consumer_secret_ciphertext, key=key) == "consumer-secret-private"
    assert decrypt_credential(stored.passkey_ciphertext, key=key) == "passkey-private"
    assert response.integration_id == stored.integration_id
    assert response.stk_callback_url == f"https://pay.example.test/v1/callbacks/stk/{stored.integration_id}"
    assert response.c2b_validation_url.endswith(f"/v1/callbacks/c2b/validation/{stored.integration_id}")
    assert response.c2b_enabled is False
    assert response.c2b_registration_status == "not_requested"
    assert "consumer_key" not in response.model_dump()
    assert "consumer_secret" not in response.model_dump()
    assert "passkey" not in response.model_dump()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_daraja_credentials_are_not_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid provider credentials never create an active integration."""
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr("app.api.integrations.get_settings", lambda: _settings(key))

    async def reject(**kwargs: object) -> None:
        raise DarajaCredentialsRejected("safe internal error")

    monkeypatch.setattr("app.api.integrations.validate_daraja_credentials", reject)
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(None))
    session.add = MagicMock()
    session.commit = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await create_integration(_body(), _principal(), session)
    assert error.value.status_code == 422
    assert error.value.detail == "daraja_credentials_invalid"
    session.add.assert_not_called()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_encryption_key_fails_before_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """The route does not call Daraja or persist credentials without an encryption key."""
    monkeypatch.setattr("app.api.integrations.get_settings", lambda: _settings(None))
    provider = AsyncMock()
    monkeypatch.setattr("app.api.integrations.validate_daraja_credentials", provider)
    session = MagicMock()
    session.exec = AsyncMock()
    session.add = MagicMock()

    with pytest.raises(HTTPException) as error:
        await create_integration(_body(), _principal(), session)
    assert error.value.status_code == 503
    assert error.value.detail == "credential_encryption_not_configured"
    provider.assert_not_awaited()
    session.exec.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_provider_unavailable_is_a_safe_retryable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Network/provider errors are sanitized and do not persist credentials."""
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr("app.api.integrations.get_settings", lambda: _settings(key))

    async def unavailable(**kwargs: object) -> None:
        raise DarajaUnavailable("provider detail must not leak")

    monkeypatch.setattr("app.api.integrations.validate_daraja_credentials", unavailable)
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(None))
    session.add = MagicMock()

    with pytest.raises(HTTPException) as error:
        await create_integration(_body(), _principal(), session)
    assert error.value.status_code == 503
    assert error.value.detail == "daraja_authorization_unavailable"
    assert "provider detail" not in str(error.value.detail)
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_duplicate_integration_is_rejected_before_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A merchant cannot create a second Daraja integration for the same environment."""
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr("app.api.integrations.get_settings", lambda: _settings(key))
    existing = DarajaIntegration(
        merchant_id=uuid4(),
        environment="sandbox",
        integration_id="int_existing",
    )
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(existing))
    provider = AsyncMock()
    monkeypatch.setattr("app.api.integrations.validate_daraja_credentials", provider)

    with pytest.raises(HTTPException) as error:
        await create_integration(_body(), _principal(existing.merchant_id), session)
    assert error.value.status_code == 409
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_integration_detail_is_scoped_to_authenticated_merchant() -> None:
    """Knowing another merchant's opaque integration ID does not permit access."""
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(None))
    with pytest.raises(HTTPException) as error:
        await get_integration("int_some-other-merchant", _principal(), session)
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_integration_list_uses_a_typed_safe_response() -> None:
    """List responses do not expose credential columns."""
    record = DarajaIntegration(
        merchant_id=uuid4(),
        environment="sandbox",
        integration_id="int_safe",
        shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        status="active",
        credential_status="valid",
        consumer_key_ciphertext=b"ciphertext",
        consumer_secret_ciphertext=b"ciphertext",
        passkey_ciphertext=b"ciphertext",
    )
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result([record]))
    response = await list_integrations(_principal(record.merchant_id), session)
    assert len(response) == 1
    assert response[0].integration_id == "int_safe"
    assert "consumer_key_ciphertext" not in response[0].model_dump()
    assert "passkey_ciphertext" not in response[0].model_dump()
