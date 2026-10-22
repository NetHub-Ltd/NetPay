"""Unit tests for machine secret hashing and signed access tokens."""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.api.oauth import TokenRequest, create_access_token
from app.api.provisioning import M2MClientCreateRequest, provision_m2m_client
from app.core.machine_auth import (
    decode_machine_access_token,
    create_m2m_client,
    hash_client_secret,
    issue_machine_access_token,
    verify_client_secret,
)
from app.models.merchants import M2MClient, Merchant


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


@pytest.mark.asyncio
async def test_client_creation_returns_secret_once_and_stores_only_hash() -> None:
    """Provisioning helper persists only a hash and returns the plaintext separately."""
    session = MagicMock()
    session.flush = AsyncMock()
    result = await create_m2m_client(
        session,
        merchant_id=uuid4(),
        scopes=["payments:read"],
    )
    assert result.client.client_id.startswith("nmc_")
    assert result.client_secret.startswith("nms_")
    assert result.client.secret_hash != result.client_secret
    assert verify_client_secret(result.client_secret, result.client.secret_hash)
    session.add.assert_called_once_with(result.client)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_creation_rejects_unsupported_scopes_before_persistence() -> None:
    """Client provisioning cannot grant undeclared administrative scopes."""
    session = MagicMock()
    session.flush = AsyncMock()
    with pytest.raises(ValueError):
        await create_m2m_client(session, merchant_id=uuid4(), scopes=["admin:*"])
    session.add.assert_not_called()


def test_production_rejects_the_development_signing_key() -> None:
    """The checked-in development key cannot sign production machine tokens."""
    settings = Settings(environment="production")
    with pytest.raises(RuntimeError):
        issue_machine_access_token(
            client_id="nmc_test-client",
            merchant_id=uuid4(),
            scopes=["payments:read"],
            settings=settings,
        )


def _scalar_result(value: object) -> MagicMock:
    """Build the minimal SQLModel result surface used by the token endpoint."""
    result = MagicMock()
    result.first.return_value = value
    return result


@pytest.mark.asyncio
async def test_token_endpoint_issues_token_only_after_client_and_merchant_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token endpoint validates stored secret and active merchant before issuing a token."""
    settings = _settings()
    monkeypatch.setattr("app.api.oauth.get_settings", lambda: settings)
    merchant = Merchant(name="Example Merchant", slug="example-merchant", status="active")
    secret = "nms_" + "a" * 48
    client = M2MClient(
        merchant_id=merchant.id,
        client_id="nmc_test-client",
        secret_hash=hash_client_secret(secret),
        scopes=["payments:read"],
        status="active",
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_scalar_result(client), _scalar_result(merchant)])
    session.commit = AsyncMock()

    response = await create_access_token(
        TokenRequest(grant_type="client_credentials", client_id=client.client_id, client_secret=secret),
        session,
    )
    principal = decode_machine_access_token(response.access_token, settings=settings)
    assert response.token_type == "Bearer"
    assert response.expires_in == 300
    assert principal.client_id == client.client_id
    assert principal.merchant_id == merchant.id
    assert principal.scopes == frozenset({"payments:read"})
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_token_endpoint_rejects_invalid_client_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid secrets do not produce tokens or commit client usage."""
    from fastapi import HTTPException

    settings = _settings()
    monkeypatch.setattr("app.api.oauth.get_settings", lambda: settings)
    merchant = Merchant(name="Example Merchant", slug="example-merchant", status="active")
    client = M2MClient(
        merchant_id=merchant.id,
        client_id="nmc_test-client",
        secret_hash=hash_client_secret("nms_" + "a" * 48),
        scopes=["payments:read"],
        status="active",
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_scalar_result(client), _scalar_result(merchant)])
    session.commit = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await create_access_token(
            TokenRequest(
                grant_type="client_credentials",
                client_id=client.client_id,
                client_secret="nms_" + "b" * 48,
            ),
            session,
        )
    assert error.value.status_code == 401
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_operator_provisioning_returns_secret_once_and_persists_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only a valid operator key can create a client; response contains secret once."""
    from pydantic import SecretStr

    settings = _settings()
    settings.m2m_provisioning_key = SecretStr("operator-provisioning-key-that-is-long-enough")
    monkeypatch.setattr("app.api.provisioning.get_settings", lambda: settings)
    merchant = Merchant(name="Provisioned Merchant", slug="provisioned-merchant", status="active")
    session = MagicMock()
    session.exec = AsyncMock(return_value=_scalar_result(merchant))
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    response = await provision_m2m_client(
        M2MClientCreateRequest(merchant_id=merchant.id, scopes=["payments:read"]),
        provisioning_key="operator-provisioning-key-that-is-long-enough",
        session=session,
    )
    stored_client = session.add.call_args.args[0]
    assert response.client_id == stored_client.client_id
    assert response.client_secret.startswith("nms_")
    assert response.merchant_id == merchant.id
    assert response.scopes == ["payments:read"]
    assert response.client_secret != stored_client.secret_hash
    assert verify_client_secret(response.client_secret, stored_client.secret_hash)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_operator_provisioning_rejects_wrong_key_before_database_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid operator keys cannot inspect merchants or create credentials."""
    from fastapi import HTTPException
    from pydantic import SecretStr

    settings = _settings()
    settings.m2m_provisioning_key = SecretStr("operator-provisioning-key-that-is-long-enough")
    monkeypatch.setattr("app.api.provisioning.get_settings", lambda: settings)
    session = MagicMock()
    session.exec = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await provision_m2m_client(
            M2MClientCreateRequest(merchant_id=uuid4(), scopes=["payments:read"]),
            provisioning_key="incorrect-operator-key",
            session=session,
        )
    assert error.value.status_code == 401
    session.exec.assert_not_awaited()


@pytest.mark.asyncio
async def test_operator_provisioning_is_disabled_without_configured_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The operator route is hidden when no sufficiently long key is configured."""
    from fastapi import HTTPException

    settings = _settings()
    settings.m2m_provisioning_key = None
    monkeypatch.setattr("app.api.provisioning.get_settings", lambda: settings)
    session = MagicMock()
    session.exec = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await provision_m2m_client(
            M2MClientCreateRequest(merchant_id=uuid4(), scopes=["payments:read"]),
            provisioning_key=None,
            session=session,
        )
    assert error.value.status_code == 404
    session.exec.assert_not_awaited()
