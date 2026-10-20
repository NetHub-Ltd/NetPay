"""Small, typed Daraja OAuth client.

Fetching an OAuth token validates consumer key/secret authentication only. It
must not be described as proof that a shortcode or passkey is valid.
"""

from typing import Literal

import httpx

Environment = Literal["sandbox", "production"]

_BASE_URLS: dict[Environment, str] = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class InvalidDarajaCredentials(Exception):
    """Daraja rejected the configured consumer credentials."""


class DarajaUnavailable(Exception):
    """Daraja could not be reached or returned an unusable response."""


async def request_access_token(
    environment: Environment,
    consumer_key: str,
    consumer_secret: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    """Request an OAuth token; never log or return the token to API callers."""
    url = f"{_BASE_URLS[environment]}/oauth/v1/generate"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, transport=transport) as client:
            response = await client.get(
                url,
                params={"grant_type": "client_credentials"},
                auth=(consumer_key, consumer_secret),
            )
    except httpx.RequestError as exc:
        raise DarajaUnavailable("Daraja OAuth endpoint is unavailable") from exc

    if response.status_code in {400, 401, 403}:
        raise InvalidDarajaCredentials("Daraja rejected the consumer credentials")
    if response.status_code < 200 or response.status_code >= 300:
        raise DarajaUnavailable("Daraja OAuth endpoint returned an error")

    try:
        payload = response.json()
        token = payload.get("access_token")
    except (ValueError, AttributeError) as exc:
        raise DarajaUnavailable("Daraja OAuth response was invalid") from exc
    if not isinstance(token, str) or not token:
        raise DarajaUnavailable("Daraja OAuth response did not include an access token")
    return token
