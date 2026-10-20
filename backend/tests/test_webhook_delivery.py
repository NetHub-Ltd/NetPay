import asyncio
import hashlib
import hmac
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session

from app.config import get_settings
from app.crypto import encrypt_secret
from app.models import EventDeliveryAttempt, EventDestination, EventOutbox, Merchant
from app.worker import dispatch_outbox_once


def _sync_url() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)


@pytest.mark.asyncio
async def test_outbox_delivery_is_signed_and_recorded(monkeypatch) -> None:
    engine = create_engine(_sync_url())
    now = datetime.now(timezone.utc)
    merchant = Merchant(name=f"Webhook merchant {uuid4()}", status="active", created_at=now, updated_at=now)
    signing_secret = "webhook-signing-secret-for-test"
    event_id = uuid4()
    event = EventOutbox(
        event_id=event_id,
        merchant_id=merchant.id,
        aggregate_id=uuid4(),
        event_type="payment.succeeded",
        schema_version=1,
        payload={"event_id": str(event_id), "status": "succeeded"},
        delivery_status="pending",
        attempts=0,
        next_attempt_at=now,
        created_at=now,
    )
    destination = EventDestination(
        merchant_id=merchant.id,
        url="https://webhook.example.test/payments",
        signing_secret_ciphertext=encrypt_secret(signing_secret),
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    with Session(engine) as session:
        session.add(merchant)
        session.add(destination)
        session.add(event)
        session.commit()
    engine.dispose()

    monkeypatch.setattr("app.worker.validate_public_https_url", lambda _url: None)
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(204)

    async_engine = create_async_engine(get_settings().database_url)
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            processed = await dispatch_outbox_once(session, transport=httpx.MockTransport(handler))
    finally:
        await async_engine.dispose()

    assert processed == 1
    assert len(captured) == 1
    request = captured[0]
    body = request.content
    expected_signature = hmac.new(signing_secret.encode(), body, hashlib.sha256).hexdigest()
    assert request.headers["X-NetPay-Event-Id"] == str(event_id)
    assert request.headers["X-NetPay-Signature"] == f"sha256={expected_signature}"
    assert request.headers["Idempotency-Key"] == str(event_id)

    engine = create_engine(_sync_url())
    with Session(engine) as session:
        saved_event = session.exec(select(EventOutbox).where(EventOutbox.event_id == event_id)).one()
        attempts = session.exec(select(EventDeliveryAttempt).where(EventDeliveryAttempt.outbox_event_id == saved_event.id)).all()
    engine.dispose()
    assert saved_event.delivery_status == "delivered"
    assert len(attempts) == 1
    assert attempts[0].outcome == "delivered"


def test_webhook_url_validator_blocks_private_and_non_https_destinations(monkeypatch) -> None:
    from app.webhooks.url_validation import UnsafeWebhookURL, validate_public_https_url

    with pytest.raises(UnsafeWebhookURL):
        validate_public_https_url("https://127.0.0.1/hook")
    with pytest.raises(UnsafeWebhookURL):
        validate_public_https_url("http://example.com/hook")

    monkeypatch.setattr(
        "app.webhooks.url_validation.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("8.8.8.8", 443))],
    )
    validate_public_https_url("https://hooks.example.com/payments")
