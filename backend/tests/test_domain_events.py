"""Domain event dispatcher isolates subscriber failures."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.payment_intent import PaymentIntent
from app.services.domain_events import publish_payment_settled


@pytest.mark.asyncio
async def test_live_notify_runs_even_if_webhooks_fail():
    intent = PaymentIntent(
        id=uuid4(),
        tenant_id=uuid4(),
        integration_id=uuid4(),
        status="succeeded",
        amount_minor=100,
        currency="KES",
        phone="254700000000",
    )
    session = AsyncMock()
    with (
        patch("app.services.domain_events.fanout_webhooks", new_callable=AsyncMock) as wh,
        patch("app.services.domain_events.publish_notification", new_callable=AsyncMock) as live,
    ):
        wh.side_effect = RuntimeError("webhook boom")
        await publish_payment_settled(session, intent, transaction_id="ABC")
        live.assert_awaited()
