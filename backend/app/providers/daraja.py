"""Safe HTTP client for the Daraja Authorization API."""
from __future__ import annotations

import base64
from datetime import datetime
from zoneinfo import ZoneInfo

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



class DarajaStkRejected(RuntimeError):
    """Raised when Daraja definitively rejects an STK request."""

    def __init__(self, safe_code: str = "daraja_rejected") -> None:
        super().__init__(safe_code)
        self.safe_code = safe_code


class DarajaStkUncertain(RuntimeError):
    """Raised when the STK outcome cannot be determined safely."""


async def _get_access_token(
    *,
    environment: str,
    consumer_key: str,
    consumer_secret: str,
    timeout_seconds: float,
) -> str:
    """Obtain a short-lived OAuth token without exposing provider response details."""
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
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise DarajaUnavailable("Daraja authorization response did not contain a token")
    return token


async def initiate_stk_push(
    *,
    environment: str,
    consumer_key: str,
    consumer_secret: str,
    passkey: str,
    shortcode: str,
    party_b_shortcode: str,
    product_type: str,
    phone_number: str,
    amount_kes: int,
    callback_url: str,
    account_reference: str,
    transaction_description: str,
    timeout_seconds: float,
) -> dict[str, str]:
    """Initiate one STK request; an acknowledgement is not proof of payment success."""
    base_url = _DARAJA_BASE_URLS.get(environment)
    if base_url is None:
        raise ValueError("Unsupported Daraja environment")
    try:
        token = await _get_access_token(
            environment=environment,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            timeout_seconds=timeout_seconds,
        )
    except DarajaCredentialsRejected as exc:
        raise DarajaStkRejected("daraja_auth_rejected") from exc
    except DarajaUnavailable as exc:
        raise DarajaStkUncertain("daraja_authorization_uncertain") from exc

    timestamp = datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((shortcode + passkey + timestamp).encode("utf-8")).decode("ascii")
    transaction_type = "CustomerPayBillOnline" if product_type == "paybill" else "CustomerBuyGoodsOnline"
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": transaction_type,
        "Amount": amount_kes,
        "PartyA": phone_number,
        "PartyB": party_b_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": transaction_description[:13],
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                base_url + "/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            )
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        # The request may have reached Daraja even when the response was lost.
        raise DarajaStkUncertain("daraja_stk_outcome_unknown") from exc

    if response.status_code in {400, 401, 403, 404}:
        safe_code = "daraja_request_rejected"
        try:
            error_payload = response.json()
            if isinstance(error_payload, dict):
                raw_code = error_payload.get("errorCode")
                if isinstance(raw_code, str) and raw_code.isalnum() and len(raw_code) <= 32:
                    safe_code = raw_code
        except ValueError:
            pass
        raise DarajaStkRejected(safe_code)
    if response.status_code != 200:
        raise DarajaStkUncertain("daraja_stk_outcome_unknown")
    try:
        result = response.json()
    except ValueError as exc:
        raise DarajaStkUncertain("daraja_stk_response_unusable") from exc
    if not isinstance(result, dict):
        raise DarajaStkUncertain("daraja_stk_response_unusable")
    if str(result.get("ResponseCode")) != "0":
        raise DarajaStkRejected("daraja_request_rejected")
    checkout_id = result.get("CheckoutRequestID")
    merchant_request_id = result.get("MerchantRequestID")
    if not isinstance(checkout_id, str) or not checkout_id or not isinstance(merchant_request_id, str) or not merchant_request_id:
        raise DarajaStkUncertain("daraja_stk_response_missing_request_ids")
    return {
        "checkout_request_id": checkout_id,
        "merchant_request_id": merchant_request_id,
        "response_code": "0",
    }
