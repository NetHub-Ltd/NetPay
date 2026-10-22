"""Daraja provider adapter tests for OAuth and STK payload construction."""
import base64
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.core.credentials import decrypt_credential, encrypt_credential
from app.models.integrations import DarajaIntegration
from app.providers import daraja


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeAsyncClient:
    def __init__(self, timeout: float, *, fail_post: bool = False) -> None:
        self.timeout = timeout
        self.fail_post = fail_post
        self.get_call: dict[str, Any] | None = None
        self.post_call: dict[str, Any] | None = None

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.get_call = {"url": url, **kwargs}
        return FakeResponse(200, {"access_token": "test-provider-token", "expires_in": "3599"})

    async def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.post_call = {"url": url, **kwargs}
        if self.fail_post:
            raise httpx.TimeoutException("private timeout detail")
        return FakeResponse(
            200,
            {
                "ResponseCode": "0",
                "CheckoutRequestID": "ws_CO_test",
                "MerchantRequestID": "merchant-test",
            },
        )


@pytest.mark.asyncio
async def test_stk_payload_uses_till_transaction_type_and_correct_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """STK payload follows official Daraja field names and password construction."""
    clients: list[FakeAsyncClient] = []

    def client_factory(timeout: float) -> FakeAsyncClient:
        client = FakeAsyncClient(timeout)
        clients.append(client)
        return client

    monkeypatch.setattr(daraja.httpx, "AsyncClient", client_factory)
    result = await daraja.initiate_stk_push(
        environment="sandbox",
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        passkey="test-passkey",
        shortcode="174379",
        party_b_shortcode="123456",
        product_type="till",
        phone_number="254712345678",
        amount_kes=100,
        callback_url="https://pay.example.test/v1/callbacks/stk/int_test",
        account_reference="NP1234567890",
        transaction_description="Order payment",
        timeout_seconds=4,
    )
    assert result["checkout_request_id"] == "ws_CO_test"
    assert clients[0].timeout == 4
    assert clients[0].get_call is not None
    assert clients[0].get_call["url"] == "https://sandbox.safaricom.co.ke/oauth/v1/generate"
    assert clients[0].get_call["params"] == {"grant_type": "client_credentials"}
    assert clients[0].get_call["auth"] == ("consumer-key", "consumer-secret")
    post = clients[1].post_call
    assert post is not None
    assert post["url"] == "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    assert post["headers"]["Authorization"] == "Bearer test-provider-token"
    payload = post["json"]
    assert payload["TransactionType"] == "CustomerBuyGoodsOnline"
    assert payload["Amount"] == 100
    assert payload["PartyA"] == "254712345678"
    assert payload["PartyB"] == "123456"
    assert payload["AccountReference"] == "NP1234567890"
    assert payload["TransactionDesc"] == "Order payment"
    assert re.fullmatch(r"\d{14}", payload["Timestamp"])
    decoded_password = base64.b64decode(payload["Password"]).decode("utf-8")
    assert decoded_password == "174379test-passkey" + payload["Timestamp"]


@pytest.mark.asyncio
async def test_stk_timeout_is_ambiguous_not_a_definite_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A timeout after request submission is surfaced as unknown outcome."""
    clients: list[FakeAsyncClient] = []

    def client_factory(timeout: float) -> FakeAsyncClient:
        client = FakeAsyncClient(timeout, fail_post=bool(clients))
        clients.append(client)
        return client

    monkeypatch.setattr(daraja.httpx, "AsyncClient", client_factory)
    with pytest.raises(daraja.DarajaStkUncertain):
        await daraja.initiate_stk_push(
            environment="sandbox",
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            passkey="test-passkey",
            shortcode="174379",
            party_b_shortcode="174379",
            product_type="paybill",
            phone_number="254712345678",
            amount_kes=1,
            callback_url="https://pay.example.test/v1/callbacks/stk/int_test",
            account_reference="NP1234567890",
            transaction_description="Payment",
            timeout_seconds=4,
        )


@pytest.mark.asyncio
async def test_invalid_provider_response_is_rejected_without_raw_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provider response details do not leak through the safe exception."""
    class RejectingClient(FakeAsyncClient):
        async def post(self, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(400, {"errorCode": "40000202", "errorMessage": "contains private details"})

    monkeypatch.setattr(daraja.httpx, "AsyncClient", lambda timeout: RejectingClient(timeout))
    with pytest.raises(daraja.DarajaStkRejected) as error:
        await daraja.initiate_stk_push(
            environment="sandbox",
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            passkey="test-passkey",
            shortcode="174379",
            party_b_shortcode="174379",
            product_type="paybill",
            phone_number="254712345678",
            amount_kes=1,
            callback_url="https://pay.example.test/v1/callbacks/stk/int_test",
            account_reference="NP1234567890",
            transaction_description="Payment",
            timeout_seconds=4,
        )
    assert "private details" not in str(error.value)


def _result(value: object) -> MagicMock:
    result = MagicMock()
    result.first.return_value = value
    return result


@pytest.mark.asyncio
async def test_access_token_cache_reuses_encrypted_unexpired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid cached token is decrypted and reused without requesting a new token."""
    key = Fernet.generate_key().decode("ascii")
    integration = DarajaIntegration(
        merchant_id=uuid4(),
        integration_id="int_cached",
        environment="sandbox",
        provider_access_token_ciphertext=encrypt_credential("cached-token", key=key),
        provider_token_expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(integration))
    session.commit = AsyncMock()
    refresh = AsyncMock()
    monkeypatch.setattr(daraja, "_request_access_token", refresh)

    token = await daraja.get_or_refresh_access_token(
        session,
        integration_id=integration.id,
        environment="sandbox",
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        encryption_key=SecretStr(key),
        timeout_seconds=3,
    )
    assert token == "cached-token"
    refresh.assert_not_awaited()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_access_token_cache_encrypts_new_token_and_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refreshed provider token is encrypted and expires before provider expiry."""
    key = Fernet.generate_key().decode("ascii")
    integration = DarajaIntegration(
        merchant_id=uuid4(),
        integration_id="int_refresh",
        environment="sandbox",
    )
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(integration))
    session.commit = AsyncMock()

    async def refresh(**kwargs: object) -> tuple[str, int]:
        return "new-provider-token", 3600

    monkeypatch.setattr(daraja, "_request_access_token", refresh)
    token = await daraja.get_or_refresh_access_token(
        session,
        integration_id=integration.id,
        environment="sandbox",
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        encryption_key=SecretStr(key),
        timeout_seconds=3,
    )
    assert token == "new-provider-token"
    assert decrypt_credential(integration.provider_access_token_ciphertext, key=key) == "new-provider-token"
    assert integration.provider_token_expires_at is not None
    assert integration.provider_token_expires_at > datetime.now(UTC) + timedelta(minutes=58)
    session.commit.assert_awaited_once()
