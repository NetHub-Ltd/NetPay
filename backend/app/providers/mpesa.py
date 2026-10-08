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


def redact_token(token: str) -> str:
    """Never log a full OAuth token — prefix only."""
    if not token:
        return "(empty)"
    if len(token) <= 10:
        return token[:2] + "…"
    return f"{token[:6]}…{token[-4:]} (len={len(token)})"


async def get_access_token_meta(
    consumer_key: str,
    consumer_secret: str,
    env: MpesaEnv,
    *,
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
    skip_cache: bool = False,
) -> tuple[str, int]:
    """
    Exchange consumer key/secret for a Daraja bearer token.

    Returns (access_token, expires_in_seconds). Logs redacted token only.
    """
    cache_key = f"daraja:token:{env}:{consumer_key[:8]}"
    if not skip_cache:
        cached = await cache_get(cache_key)
        if cached:
            logger.info(
                "daraja_oauth_cache event=hit env={} key_prefix={}",
                env,
                consumer_key[:8],
            )
            return cached, 0
        logger.info(
            "daraja_oauth_cache event=miss env={} key_prefix={}",
            env,
            consumer_key[:8],
        )
    else:
        logger.info(
            "daraja_oauth_cache event=skip env={} key_prefix={}",
            env,
            consumer_key[:8],
        )

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
    expires_in = int(data.get("expires_in") or 3599)
    ttl = max(60, expires_in - 60)
    await cache_set(cache_key, token, ttl=ttl)
    logger.info(
        "daraja_oauth_cache event=set env={} key_prefix={} ttl={} expires_in={}",
        env,
        consumer_key[:8],
        ttl,
        expires_in,
    )
    return token, expires_in


async def get_access_token(
    consumer_key: str,
    consumer_secret: str,
    env: MpesaEnv,
    *,
    session: Optional[AsyncSession] = None,
    tenant_id: UUID | None = None,
    integration_id: UUID | None = None,
    payment_intent_id: UUID | None = None,
    skip_cache: bool = False,
) -> str:
    """Bearer token only (backward compatible for STK/tests). Prefer get_access_token_meta for expires_in."""
    token, _expires = await get_access_token_meta(
        consumer_key,
        consumer_secret,
        env,
        session=session,
        tenant_id=tenant_id,
        integration_id=integration_id,
        payment_intent_id=payment_intent_id,
        skip_cache=skip_cache,
    )
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


def _assert_callback_url(url: str, *, env: MpesaEnv, label: str) -> None:
    u = (url or "").strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        raise RuntimeError(f"{label} must be an absolute http(s) URL")
    if env == "production" and not u.startswith("https://"):
        raise RuntimeError(f"{label} must use HTTPS in production (Daraja requirement)")


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
    """
    POST /mpesa/c2b/v1/registerurl

    Tells Daraja where to POST C2B validation + confirmation for this ShortCode.
    ResponseType Completed|Cancelled: what to do if validation URL is unreachable.
    There is no public Daraja API to unregister — only re-register (sandbox) or
    Safaricom support letter (production).
    """
    rt = (response_type or "Completed").strip()
    if rt not in ("Completed", "Cancelled"):
        raise RuntimeError("ResponseType must be Completed or Cancelled")
    _assert_callback_url(confirmation_url, env=env, label="ConfirmationURL")
    _assert_callback_url(validation_url, env=env, label="ValidationURL")

    body = {
        "ShortCode": str(shortcode).strip(),
        "ResponseType": rt,
        "ConfirmationURL": confirmation_url.strip(),
        "ValidationURL": validation_url.strip(),
    }
    url = f"{daraja_base(env)}/mpesa/c2b/v1/registerurl"
    logger.info(
        "C2B registerurl env={} shortcode={} response_type={} confirmation={} validation={} token_redacted={}",
        env,
        body["ShortCode"],
        rt,
        body["ConfirmationURL"],
        body["ValidationURL"],
        redact_token(token),
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
    # Success is typically ResponseCode "0" (string) — also accept missing with ResponseDescription
    code = str(data.get("ResponseCode") or data.get("responseCode") or "")
    if code and code not in ("0", "00000000"):
        raise RuntimeError(
            f"C2B register unexpected ResponseCode={code!r} body={data}"
        )
    logger.info(
        "C2B register ok env={} shortcode={} response_code={} description={}",
        env,
        body["ShortCode"],
        code or "(none)",
        data.get("ResponseDescription") or data.get("responseDescription"),
    )
    return data
