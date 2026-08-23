from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import get_session, require_internal_api_key
from app.schemas.event import EnvelopeIn, ProcessResult
from app.services.processor import process_envelope

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_api_key)])

@router.post("/events", response_model=None)
async def ingest_event(envelope: EnvelopeIn, session: Annotated[AsyncSession, Depends(get_session)]) -> ProcessResult | dict[str, Any]:
    return await process_envelope(session, envelope)
