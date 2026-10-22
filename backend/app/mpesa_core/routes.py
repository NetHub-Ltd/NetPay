"""Public Daraja callback routes; all payloads are treated as untrusted."""
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.mpesa_core.callbacks import record_callback
from app.mpesa_core.errors import UnknownIntegration

router = APIRouter(prefix="/callbacks/mpesa", tags=["M-Pesa callbacks"])


def _session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="database_not_initialized")
    return factory


async def _read_payload(request: Request) -> dict[str, Any]:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > 256_000:
        raise HTTPException(status_code=413, detail="callback_body_too_large")
    body = await request.body()
    if len(body) > 256_000:
        raise HTTPException(status_code=413, detail="callback_body_too_large")
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="invalid_callback_json") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="callback_body_must_be_object")
    return payload


async def _record(request: Request, integration_id: str, callback_type: str, payload: dict[str, Any]):
    try:
        return await record_callback(_session_factory(request), integration_id, callback_type, payload)
    except UnknownIntegration as exc:
        logger.warning("mpesa_callback_unknown_integration callback_type={}", callback_type)
        raise HTTPException(status_code=404, detail="unknown_integration") from exc


@router.post("/stk/{integration_id}", include_in_schema=False)
async def stk_callback(integration_id: str, request: Request) -> dict[str, object]:
    """Persist an STK callback before acknowledging receipt."""
    receipt = await _record(request, integration_id, "stk", await _read_payload(request))
    return {"ResultCode": 0, "ResultDesc": receipt.status}


@router.post("/c2b/confirmation/{integration_id}", include_in_schema=False)
async def c2b_confirmation(integration_id: str, request: Request) -> dict[str, object]:
    """Persist a C2B confirmation callback idempotently."""
    receipt = await _record(request, integration_id, "c2b_confirmation", await _read_payload(request))
    return {"ResultCode": 0, "ResultDesc": receipt.status}


@router.post("/c2b/validation/{integration_id}", include_in_schema=False)
async def c2b_validation(integration_id: str, request: Request) -> dict[str, object]:
    """Validate only when the merchant explicitly enabled the validation capability."""
    receipt = await _record(request, integration_id, "c2b_validation", await _read_payload(request))
    if receipt.validation_accepted:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    return {"ResultCode": 1, "ResultDesc": "Validation is not enabled or callback data is invalid"}


@router.post("/{callback_type}/{integration_id}", include_in_schema=False)
async def asynchronous_result_callback(
    callback_type: str, integration_id: str, request: Request
) -> dict[str, object]:
    """Persist asynchronous results for gated Daraja operations."""
    allowed = {
        "transaction-status": "transaction_status",
        "account-balance": "account_balance",
        "reversal": "reversal",
        "b2c": "b2c",
        "b2b": "b2b",
        "pull-transactions": "pull_transactions",
    }
    normalized_type = allowed.get(callback_type)
    if normalized_type is None:
        raise HTTPException(status_code=404, detail="unknown_callback_type")
    receipt = await _record(request, integration_id, normalized_type, await _read_payload(request))
    return {"ResultCode": 0, "ResultDesc": receipt.status}
