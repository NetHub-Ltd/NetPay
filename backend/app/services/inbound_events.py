"""Durable inbound envelope store + process (P1-A)."""
from __future__ import annotations

import json
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.inbound_event import InboundEvent
from app.schemas.event import EnvelopeIn, ProcessResult
from app.services.edge_status import get_edge_connection_status
from app.services.live_hub import publish_edge_connection
from app.services.processor import process_envelope


async def _get_by_event_id(session: AsyncSession, event_id: str) -> InboundEvent | None:
    stmt = select(InboundEvent).where(InboundEvent.event_id == event_id)
    result = await session.exec(stmt)
    return result.first()


def _result_from_row(row: InboundEvent) -> ProcessResult | dict[str, Any]:
    if row.result_json:
        try:
            data = json.loads(row.result_json)
            return ProcessResult(**data) if isinstance(data, dict) else {"status": row.status}
        except Exception:  # noqa: BLE001
            return {"status": row.status, "message": "cached"}
    return {"status": row.status, "message": row.last_error or "cached"}


async def ingest_and_process(session: AsyncSession, envelope: EnvelopeIn) -> ProcessResult | dict[str, Any]:
    """
    Persist envelope by event_id, then process once.
    Replays of the same event_id return the stored result without re-applying business logic.
    """
    existing = await _get_by_event_id(session, envelope.event_id)
    if existing and existing.status == "processed":
        return _result_from_row(existing)
    if existing and existing.status == "dead":
        return {
            "status": "dead",
            "message": existing.last_error or "Event in dead-letter",
            "event_id": envelope.event_id,
        }

    public_id = None
    if isinstance(envelope.integration, dict):
        public_id = envelope.integration.get("public_id") or envelope.integration.get("id")

    if not existing:
        row = InboundEvent(
            event_id=envelope.event_id,
            provider=envelope.provider or "mpesa",
            event_type=envelope.event_type,
            integration_public_id=str(public_id) if public_id else None,
            payload_json=json.dumps(envelope.payload) if envelope.payload is not None else None,
            status="received",
            attempts=0,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    else:
        row = existing

    row.status = "processing"
    row.attempts = (row.attempts or 0) + 1
    session.add(row)
    await session.commit()

    try:
        result = await process_envelope(session, envelope)
        payload = result.model_dump(mode="json") if hasattr(result, "model_dump") else dict(result)
        row.status = "processed"
        row.result_json = json.dumps(payload)
        row.last_error = None
        session.add(row)
        await session.commit()
        try:
            snap = await get_edge_connection_status(session)
            await publish_edge_connection(snap)
        except Exception:  # noqa: BLE001
            pass
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("Inbound event {} failed: {}", envelope.event_id, exc)
        max_attempts = settings.inbound_event_max_attempts
        row.last_error = str(exc)[:512]
        row.status = "dead" if row.attempts >= max_attempts else "failed"
        session.add(row)
        await session.commit()
        return {
            "status": row.status,
            "message": row.last_error,
            "event_id": envelope.event_id,
            "attempts": row.attempts,
        }
