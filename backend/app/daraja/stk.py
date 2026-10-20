"""M-Pesa Express (STK Push) request adapter.

An accepted initiation is only a provider acknowledgement. Payment success is
established later by a correlated callback or a supported status query.
"""

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx

from app.daraja.client import DarajaUnavailable, request_access_token

Environment = Literal["sandbox", "production"]
ProductType = Literal["paybill", "till"]
_BASE_URLS: dict[Environment, str] = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class STKRequestRejected(Exception):
    """Daraja explicitly rejected the STK initiation request."""

    def __init__(self, result_code: str | None = None) -> None:
        self.result_code = result_code
        super().__init__("Daraja rejected the STK initiation request")


class STKOutcomeUnknown(Exception):
    """The STK request may have reached Daraja but no reliable response arrived."""


@dataclass(frozen=True, slots=True)
class STKAccepted:
    merchant_request_id: str
    checkout_request_id: str
    response_description: str


async def initiate_stk_push(
    *,
    environment: Environment,
    consumer_key: str,
    consumer_secret: str,
    passkey: str,
    business_shortcode: str,
    party_b_shortcode: str,
    product_type: ProductType,
    amount_kes: int,
    phone_number: str,
    callback_url: str,
    account_reference: str,
    description: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> STKAccepted:
    if amount_kes < 1:
        raise ValueError("STK amount must be at least one Kenyan shilling")
    if not callback_url.startswith("https://") and environment == "production":
        raise ValueError("Production callback URLs must use HTTPS")

    token = await request_access_token(environment, consumer_key, consumer_secret, transport=transport)
    timestamp = datetime.now(timezone(timedelta(hours=3))).strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{business_shortcode}{passkey}{timestamp}".encode("utf-8")).decode("ascii")
    transaction_type = "CustomerPayBillOnline" if product_type == "paybill" else "CustomerBuyGoodsOnline"
    body = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": transaction_type,
        "Amount": amount_kes,
        "PartyA": phone_number,
        "PartyB": party_b_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:13],
    }
    url = f"{_BASE_URLS[environment]}/mpesa/stkpush/v1/processrequest"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False, transport=transport) as client:
            response = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
    except httpx.RequestError as exc:
        raise STKOutcomeUnknown("STK request outcome is unknown") from exc

    if 400 <= response.status_code < 500:
        code: str | None = None
        try:
            candidate = response.json().get("errorCode")
            if isinstance(candidate, str) and len(candidate) <= 32:
                code = candidate
        except (ValueError, AttributeError):
            pass
        raise STKRequestRejected(code)
    if response.status_code >= 500 or response.status_code < 200:
        raise STKOutcomeUnknown("STK request outcome is unknown")

    try:
        result = response.json()
    except ValueError as exc:
        raise STKOutcomeUnknown("STK request outcome is unknown") from exc

    if not isinstance(result, dict):
        raise STKOutcomeUnknown("STK response was not a JSON object")
    raw_response_code = result.get("ResponseCode")
    if raw_response_code is None:
        raise STKOutcomeUnknown("STK response did not include a response code")
    response_code = str(raw_response_code)
    if response_code != "0":
        raise STKRequestRejected(response_code[:32])

    merchant_request_id = result.get("MerchantRequestID")
    checkout_request_id = result.get("CheckoutRequestID")
    if not isinstance(merchant_request_id, str) or not merchant_request_id or not isinstance(checkout_request_id, str) or not checkout_request_id:
        raise STKOutcomeUnknown("STK response did not include correlation identifiers")

    description_text = result.get("ResponseDescription", "Request accepted for processing")
    if not isinstance(description_text, str):
        description_text = "Request accepted for processing"
    return STKAccepted(
        merchant_request_id=merchant_request_id,
        checkout_request_id=checkout_request_id,
        response_description=description_text[:250],
    )
