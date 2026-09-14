"""Daraja M-Pesa: OAuth, STK Push, C2B URL registration — all calls audited."""
from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.core.redis import cache_get, cache_set
from app.services.outbound_audit import provider_request, redact_provider_payload

MpesaEnv = Literal["sandbox", "production"]


class StkPushError(RuntimeError):
    def __init__(self, message: str, *, request_body=None, raw=None, http_status=None):
        super().__init__(message)
        self.request_body = request_body
        self.raw = raw
        self.http_status = http_status


def daraja_base(env: MpesaEnv) -> str:
    return "https://api.safaricom.co.ke" if env == "production" else "https://sandbox.safaricom.co.ke"


def stk_timestamp(d: datetime | None = None) -> str:
    return (d or datetime.now()).strftime("%Y%m%d%H%M%S")


def stk_password(shortcode: str, passkey: str, timestamp: str) -> str:
    return base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()


def normalize_msisdn(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9:
        return "254" + digits
    return digits


async def get_access_token(
    consumer_key: str,
    consumer_secret: str,
    env: MpesaEnv,
    *,
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
) -> str:
    cache_key = f"daraja:token:{env}:{consumer_key[:8]}"
    cached = await cache_get(cache_key)
    if cached:
        logger.debug("Daraja OAuth cache hit env={} key_prefix={}", env, consumer_key[:8])
        return cached
    basic = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    url = f"{daraja_base(env)}/oauth/v1/generate?grant_type=client_credentials"
    res = await provider_request(
        session,
        method="GET",
        url=url,
        operation="oauth_token",
        headers={"Authorization": f"Basic {basic}"},
        timeout=20.0,
        tenant_id=tenant_id,
        integration_id=integration_id,
        payment_intent_id=payment_intent_id,
    )
    if res.status_code >= 400:
        raise RuntimeError(f"Daraja OAuth failed ({res.status_code}): {res.text[:500]}")
    data = res.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Daraja OAuth: missing access_token body={res.text[:300]}")
    await cache_set(cache_key, token, ttl=int(data.get("expires_in", 3500)))
    return token


async def stk_push(
    *,
    shortcode: str,
    passkey: str,
    phone: str,
    amount: str,
    account_reference: str,
    description: str,
    callback_url: str,
    env: MpesaEnv,
    token: str,
    transaction_type: str = "CustomerPayBillOnline",
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
) -> dict[str, Any]:
    ts = stk_timestamp()
    body = {
        "BusinessShortCode": shortcode,
        "Password": stk_password(shortcode, passkey, ts),
        "Timestamp": ts,
        "TransactionType": transaction_type,
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:32],
    }
    url = f"{daraja_base(env)}/mpesa/stkpush/v1/processrequest"
    logger.info("STK push shortcode={} phone={} callback={}", shortcode, phone, callback_url)
    res = await provider_request(
        session,
        method="POST",
        url=url,
        operation="stk_push",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json_body=body,
        timeout=30.0,
        tenant_id=tenant_id,
        integration_id=integration_id,
        payment_intent_id=payment_intent_id,
    )
    data = res.json() if res.content else {}
    result = {
        "checkout_request_id": data.get("CheckoutRequestID"),
        "merchant_request_id": data.get("MerchantRequestID"),
        "response_code": data.get("ResponseCode"),
        "customer_message": data.get("CustomerMessage"),
        "raw": data,
        "request_body": redact_provider_payload(body),
        "http_status": res.status_code,
        "response_text": res.text[:2000] if res.content else "",
    }
    if res.status_code >= 400 or str(data.get("ResponseCode", "0")) not in ("0",):
        raise StkPushError(
            f"STK failed status={res.status_code}: {data or res.text[:400]}",
            request_body=redact_provider_payload(body),
            raw=data or {"text": res.text[:2000]},
            http_status=res.status_code,
        )
    return result



async def stk_query(
    *,
    shortcode: str,
    passkey: str,
    checkout_request_id: str,
    env: MpesaEnv,
    token: str,
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
) -> dict[str, Any]:
    """Ask Daraja for the current STK status (M-Pesa is source of truth)."""
    ts = stk_timestamp()
    body = {
        "BusinessShortCode": shortcode,
        "Password": stk_password(shortcode, passkey, ts),
        "Timestamp": ts,
        "CheckoutRequestID": checkout_request_id,
    }
    url = f"{daraja_base(env)}/mpesa/stkpushquery/v1/query"
    logger.info("STK query checkout={}", checkout_request_id)
    res = await provider_request(
        session,
        method="POST",
        url=url,
        operation="stk_query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json_body=body,
        timeout=30.0,
        tenant_id=tenant_id,
        integration_id=integration_id,
        payment_intent_id=payment_intent_id,
    )
    data = res.json() if res.content else {}
    result = {
        "raw": data,
        "http_status": res.status_code,
        "result_code": data.get("ResultCode"),
        "result_desc": data.get("ResultDesc") or data.get("ResponseDescription"),
        "response_code": data.get("ResponseCode"),
        "checkout_request_id": data.get("CheckoutRequestID") or checkout_request_id,
        "request_body": redact_provider_payload(body),
    }
    if res.status_code >= 400:
        raise RuntimeError(f"STK query HTTP {res.status_code}: {res.text[:400]}")
    return result


async def register_c2b_urls(
    *,
    shortcode: str,
    confirmation_url: str,
    validation_url: str,
    response_type: str,
    env: MpesaEnv,
    token: str,
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
) -> dict[str, Any]:
    body = {
        "ShortCode": shortcode,
        "ResponseType": response_type,
        "ConfirmationURL": confirmation_url,
        "ValidationURL": validation_url,
    }
    url = f"{daraja_base(env)}/mpesa/c2b/v1/registerurl"
    logger.info(
        "C2B registerurl env={} shortcode={} confirmation={} validation={}",
        env,
        shortcode,
        confirmation_url,
        validation_url,
    )
    res = await provider_request(
        session,
        method="POST",
        url=url,
        operation="c2b_register_urls",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json_body=body,
        timeout=30.0,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )
    data = res.json() if res.content else {}
    if res.status_code >= 400:
        raise RuntimeError(f"C2B register failed HTTP {res.status_code}: {res.text[:500]}")
    if data.get("errorCode") or data.get("errorMessage"):
        raise RuntimeError(
            f"C2B register rejected: {data.get('errorCode')} {data.get('errorMessage')} raw={data}"
        )
    logger.info("C2B register response: {}", data)
    return data
