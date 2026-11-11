"""Pure callback parsers; routing, trust decisions and persistence stay in NetPay."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import ValidationError

from app.mpesa_core.errors import InvalidRequest
from app.mpesa_core.schemas import AsyncResultCallback, C2BCallback, STKCallback


def _object(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InvalidRequest("callback body must be a JSON object")
    try:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise InvalidRequest("callback body is not JSON serializable") from exc
    if len(encoded.encode("utf-8")) > 128_000:
        raise InvalidRequest("callback body exceeds the supported size")
    return payload


def parse_stk_callback(payload: object) -> STKCallback:
    """Validate the Daraja STK callback envelope without declaring payment success."""
    body = _object(payload)
    try:
        return STKCallback.model_validate(body["Body"]["stkCallback"])
    except (KeyError, TypeError, ValidationError) as exc:
        raise InvalidRequest("invalid STK callback structure") from exc


def parse_c2b_callback(payload: object) -> C2BCallback:
    """Validate a C2B confirmation/validation payload."""
    try:
        return C2BCallback.model_validate(_object(payload))
    except ValidationError as exc:
        raise InvalidRequest("invalid C2B callback structure") from exc


def parse_async_result_callback(payload: object) -> AsyncResultCallback:
    """Validate a common asynchronous operation result envelope."""
    try:
        return AsyncResultCallback.model_validate(_object(payload))
    except ValidationError as exc:
        raise InvalidRequest("invalid asynchronous result callback structure") from exc


def callback_fingerprint(payload: object) -> str:
    """Return a deterministic fingerprint for deduplication; caller persists it."""
    encoded = json.dumps(_object(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
