from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session, require_internal_api_key
from app.schemas.event import EnvelopeIn, ProcessResult
from app.services.inbound_events import ingest_and_process
from app.services.timeouts import expire_stale_intents

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_api_key)],
)


@router.post("/events", response_model=None)
async def ingest_event(
    envelope: EnvelopeIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProcessResult | dict[str, Any]:
    """Persist envelope (unique event_id) then process; replays return cached result."""
    return await ingest_and_process(session, envelope)


@router.post("/expire-stale")
async def expire_stale(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Expire provider_requested intents past STK_TIMEOUT_SECONDS (ops / cron)."""
    return await expire_stale_intents(session)
