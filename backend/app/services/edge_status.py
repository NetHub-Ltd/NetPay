"""Edge → NetPay connection visibility (UX-B)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inbound_event import InboundEvent


async def get_edge_connection_status(session: AsyncSession) -> dict[str, Any]:
    """Summarize recent inbound_events from the edge worker."""
    now = datetime.now(timezone.utc)
    quiet_after = timedelta(minutes=15)

    last_any: Optional[InboundEvent] = None
    last_hb: Optional[InboundEvent] = None
    dead_recent = 0

    stmt = (
        select(InboundEvent)
        .where(col(InboundEvent.deleted_at).is_(None))
        .order_by(col(InboundEvent.created_at).desc())
        .limit(200)
    )
    rows = list((await session.exec(stmt)).all())
    for row in rows:
        if last_any is None:
            last_any = row
        et = (row.event_type or "").lower()
        if last_hb is None and ("heartbeat" in et or et in {"edge.ping", "edge_ping"}):
            last_hb = row
        if row.status == "dead" and row.created_at and row.created_at >= now - timedelta(hours=24):
            dead_recent += 1

    def iso(dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    last_at = last_any.created_at if last_any else None
    hb_at = last_hb.created_at if last_hb else None

    # Prefer heartbeat for "connected" if present; else any inbound
    signal_at = hb_at or last_at
    if signal_at is None:
        link = "never"
        label = "No messages from the edge yet"
    else:
        if signal_at.tzinfo is None:
            signal_at = signal_at.replace(tzinfo=timezone.utc)
        age = now - signal_at
        if dead_recent > 0 and (last_any and last_any.status == "dead"):
            link = "errors"
            label = "Recent delivery problems — check edge secrets and DLQ"
        elif age <= quiet_after:
            link = "connected"
            label = "Edge is delivering messages"
        else:
            link = "quiet"
            label = "No recent edge messages (normal if no payments)"

    return {
        "status": link,
        "label": label,
        "last_inbound_at": iso(last_at),
        "last_inbound_event_type": last_any.event_type if last_any else None,
        "last_inbound_status": last_any.status if last_any else None,
        "last_heartbeat_at": iso(hb_at),
        "dead_events_last_24h": dead_recent,
    }
