import httpx
import pytest

from app.daraja.client import (
    DarajaUnavailable,
    InvalidDarajaCredentials,
    request_access_token,
)


@pytest.mark.asyncio
async def test_oauth_returns_token_from_successful_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/oauth/v1/generate"
        assert request.url.params["grant_type"] == "client_credentials"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(200, json={"access_token": "test-token", "expires_in": 3599})

    token = await request_access_token(
        "sandbox", "consumer-key", "consumer-secret", transport=httpx.MockTransport(handler)
    )

    assert token == "test-token"


@pytest.mark.asyncio
async def test_oauth_rejection_is_classified_as_invalid_credentials() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(401, json={"error": "invalid_client"}))

    with pytest.raises(InvalidDarajaCredentials):
        await request_access_token("sandbox", "bad-key", "bad-secret", transport=transport)


@pytest.mark.asyncio
async def test_oauth_server_error_is_not_misclassified_as_bad_credentials() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(503, json={"error": "unavailable"}))

    with pytest.raises(DarajaUnavailable):
        await request_access_token("sandbox", "key", "secret", transport=transport)
