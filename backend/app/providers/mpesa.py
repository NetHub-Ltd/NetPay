"""Daraja M-Pesa: OAuth, STK Push, C2B URL registration."""
from __future__ import annotations
import base64
from datetime import datetime
from typing import Any, Literal
import httpx
from loguru import logger
from app.core.redis import cache_get, cache_set

MpesaEnv = Literal["sandbox", "production"]

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

async def get_access_token(consumer_key: str, consumer_secret: str, env: MpesaEnv) -> str:
    cache_key = f"daraja:token:{env}:{consumer_key[:8]}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    basic = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    url = f"{daraja_base(env)}/oauth/v1/generate?grant_type=client_credentials"
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(url, headers={"Authorization": f"Basic {basic}"})
    if res.status_code >= 400:
        raise RuntimeError(f"Daraja OAuth failed ({res.status_code}): {res.text[:240]}")
    data = res.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Daraja OAuth: missing access_token")
    await cache_set(cache_key, token, ttl=int(data.get("expires_in", 3500)))
    return token

async def stk_push(*, shortcode: str, passkey: str, phone: str, amount: str, account_reference: str,
                   description: str, callback_url: str, env: MpesaEnv, token: str,
                   transaction_type: str = "CustomerPayBillOnline") -> dict[str, Any]:
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
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
    data = res.json() if res.content else {}
    if res.status_code >= 400 or data.get("ResponseCode") not in ("0", 0, None):
        if data.get("ResponseCode") not in ("0", 0):
            raise RuntimeError(f"STK failed: {data}")
    return {
        "checkout_request_id": data.get("CheckoutRequestID"),
        "merchant_request_id": data.get("MerchantRequestID"),
        "response_code": data.get("ResponseCode"),
        "customer_message": data.get("CustomerMessage"),
        "raw": data,
    }

async def register_c2b_urls(*, shortcode: str, confirmation_url: str, validation_url: str,
                            response_type: str, env: MpesaEnv, token: str) -> dict[str, Any]:
    body = {
        "ShortCode": shortcode,
        "ResponseType": response_type,
        "ConfirmationURL": confirmation_url,
        "ValidationURL": validation_url,
    }
    url = f"{daraja_base(env)}/mpesa/c2b/v1/registerurl"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
    data = res.json() if res.content else {}
    if res.status_code >= 400:
        raise RuntimeError(f"C2B register failed ({res.status_code}): {res.text[:240]}")
    return data
