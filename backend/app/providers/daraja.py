"""Safe HTTP client for the Daraja Authorization API."""
from __future__ import annotations

import httpx

_DARAJA_BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class DarajaCredentialsRejected(RuntimeError):
    """Raised when Daraja rejects the submitted consumer credentials."""


class DarajaUnavailable(RuntimeError):
    """Raised when the provider cannot be reached or returns an unusable response."""


async def validate_daraja_credentials(
    *,
    environment: str,
    consumer_key: str,
    consumer_secret: str,
    timeout_seconds: float,
) -> None:
    """Validate consumer credentials by requesting a short-lived OAuth token.

    The returned token is deliberately discarded. No credentials, authorization
    headers, response bodies, or provider tokens are logged or included in errors.
    """
    base_url = _DARAJA_BASE_URLS.get(environment)
    if base_url is None:
        raise ValueError("Unsupported Daraja environment")
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(
                base_url + "/oauth/v1/generate",
                params={"grant_type": "client_credentials"},
                auth=(consumer_key, consumer_secret),
            )
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise DarajaUnavailable("Daraja authorization endpoint is unavailable") from exc

    if response.status_code in {400, 401, 403}:
        raise DarajaCredentialsRejected("Daraja rejected the submitted consumer credentials")
    if response.status_code != 200:
        raise DarajaUnavailable("Daraja authorization endpoint returned an unexpected status")

    try:
        payload = response.json()
    except ValueError as exc:
        raise DarajaUnavailable("Daraja authorization response was not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str) or not payload["access_token"]:
        raise DarajaCredentialsRejected("Daraja did not issue an access token for these credentials")
