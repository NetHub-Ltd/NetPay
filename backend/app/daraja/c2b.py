"""Opt-in C2B callback URL registration adapter."""

from typing import Literal

import httpx

from app.daraja.client import DarajaUnavailable, InvalidDarajaCredentials, request_access_token

Environment = Literal["sandbox", "production"]
_BASE_URLS: dict[Environment, str] = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class C2BRegistrationRejected(Exception):
    """Daraja explicitly rejected C2B URL registration."""


class C2BRegistrationUnknown(Exception):
    """Registration may have succeeded, but no reliable response arrived."""


async def register_c2b_urls(
    *,
    environment: Environment,
    consumer_key: str,
    consumer_secret: str,
    shortcode: str,
    validation_url: str,
    confirmation_url: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    if environment == "production" and (
        not validation_url.startswith("https://") or not confirmation_url.startswith("https://")
    ):
        raise ValueError("Production C2B URLs must use HTTPS")

    # Token failures occur before registration is submitted, so callers may safely
    # report a definite failure. Network ambiguity after POST must not be retried
    # blindly in production because registration is documented as one-time.
    token = await request_access_token(environment, consumer_key, consumer_secret, transport=transport)
    url = f"{_BASE_URLS[environment]}/mpesa/c2b/v1/registerurl"
    body = {
        "ShortCode": shortcode,
        "ResponseType": "Completed",
        "ConfirmationURL": confirmation_url,
        "ValidationURL": validation_url,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False, transport=transport) as client:
            response = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
    except httpx.RequestError as exc:
        raise C2BRegistrationUnknown("C2B registration outcome is unknown") from exc

    if 400 <= response.status_code < 500:
        raise C2BRegistrationRejected("Daraja rejected C2B URL registration")
    if response.status_code >= 500 or response.status_code < 200:
        raise C2BRegistrationUnknown("C2B registration outcome is unknown")
    try:
        result = response.json()
    except ValueError as exc:
        raise C2BRegistrationUnknown("C2B registration outcome is unknown") from exc
    if not isinstance(result, dict):
        raise C2BRegistrationUnknown("C2B registration response was not a JSON object")
    response_code = result.get("ResponseCode")
    if response_code is None:
        raise C2BRegistrationUnknown("C2B registration response was incomplete")
    if str(response_code) != "0":
        raise C2BRegistrationRejected("Daraja rejected C2B URL registration")
