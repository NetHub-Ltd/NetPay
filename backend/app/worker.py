"""Recover unmatched callbacks and dispatch durable webhook outbox events.

Run as a second process from the same application image. PostgreSQL owns all
work state; Redis is not required for correctness or recovery.
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.crypto import CredentialEncryptionError, decrypt_secret
from app.models import DarajaIntegration, EventDeliveryAttempt, EventDestination, EventOutbox, Payment, PaymentAttempt, ProviderCallback
from app.payments.outbox import payment_event
from app.routers.payments import _apply_early_callback
from app.webhooks.url_validation import UnsafeWebhookURL, validate_public_https_url

_MAX_ATTEMPTS = 12
_BATCH_SIZE = 25
_DELIVERY_LEASE = timedelta(minutes=5)


async def reconcile_unmatched_callbacks(session: AsyncSession, batch_size: int = 100) -> int:
    """Resolve callbacks that raced ahead of the STK response persistence."""
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(hours=24)

    # Retire old unmatched callbacks in bounded batches so they cannot starve
    # callbacks that have a chance of matching a recently persisted STK request.
    stale_result = await session.exec(
        select(ProviderCallback)
        .where(
            ProviderCallback.processing_status == "unmatched",
            ProviderCallback.received_at <= stale_cutoff,
        )
        .order_by(ProviderCallback.received_at.asc())
        .limit(batch_size)
    )
    stale_records = list(stale_result.all())
    for stale_record in stale_records:
        stale_record.processing_status = "manual_review"
        stale_record.processed_at = now
        session.add(stale_record)
    if stale_records:
        await session.commit()

    result = await session.exec(
        select(ProviderCallback)
        .where(
            ProviderCallback.processing_status == "unmatched",
            ProviderCallback.received_at > stale_cutoff,
        )
        .order_by(ProviderCallback.received_at.desc())
        .limit(batch_size)
    )
    recovered = 0
    for callback in result.all():
        checkout_id = callback.safe_payload.get("checkout_request_id")
        if not isinstance(checkout_id, str) or not checkout_id:
            continue
        payment_result = await session.exec(
            select(Payment)
            .where(
                Payment.integration_id == callback.integration_id,
                Payment.provider_checkout_request_id == checkout_id,
            )
            .with_for_update()
        )
        payment = payment_result.first()
        if payment is None:
            continue
        integration = await session.get(DarajaIntegration, callback.integration_id)
        if integration is None:
            continue
        event_type = await _apply_early_callback(session, integration, payment, checkout_id)
        payment.updated_at = datetime.now(timezone.utc)
        session.add(payment)
        if event_type is not None:
            session.add(payment_event(payment, event_type))
        await session.commit()
        recovered += 1
    return recovered


async def recover_stale_submissions(session: AsyncSession, batch_size: int = 100) -> int:
    """Move abandoned provider submissions to unknown rather than retrying blindly."""
    recovered = 0
    for _ in range(batch_size):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
        result = await session.exec(
            select(PaymentAttempt)
            .where(
                PaymentAttempt.outcome.in_(["submitting", "recovering"]),
                PaymentAttempt.updated_at <= cutoff,
            )
            .order_by(PaymentAttempt.updated_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        attempt = result.first()
        if attempt is None:
            break

        # Lease one row at a time so a commit cannot release locks on a batch
        # that another worker may then recover concurrently.
        attempt.outcome = "recovering"
        attempt.updated_at = datetime.now(timezone.utc)
        session.add(attempt)
        await session.commit()

        payment = await session.get(Payment, attempt.payment_id)
        if payment is None or payment.status != "pending" or payment.provider_checkout_request_id:
            attempt.outcome = "recovered_noop"
            attempt.updated_at = datetime.now(timezone.utc)
            session.add(attempt)
            await session.commit()
            continue

        payment.status = "unknown"
        payment.updated_at = datetime.now(timezone.utc)
        attempt.outcome = "unknown"
        attempt.safe_error_code = "worker_recovered_stale_submission"
        attempt.updated_at = datetime.now(timezone.utc)
        session.add(payment)
        session.add(attempt)
        session.add(payment_event(payment, "payment.unknown"))
        await session.commit()
        recovered += 1
    return recovered


async def _deliver_one(
    session: AsyncSession,
    event: EventOutbox,
    destination: EventDestination,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    attempt_number = event.attempts
    started = time.monotonic()
    http_status: int | None = None
    safe_error_code: str | None = None
    outcome = "failed"
    try:
        await asyncio.to_thread(validate_public_https_url, destination.url)
        signing_secret = decrypt_secret(destination.signing_secret_ciphertext)
        body = json.dumps(event.payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-NetPay-Event-Id": str(event.event_id),
            "X-NetPay-Signature": f"sha256={signature}",
            "Idempotency-Key": str(event.event_id),
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, transport=transport) as client:
            async with client.stream("POST", destination.url, content=body, headers=headers) as response:
                http_status = response.status_code
        if 200 <= response.status_code < 300:
            outcome = "delivered"
        else:
            safe_error_code = f"http_{response.status_code}"
    except UnsafeWebhookURL:
        safe_error_code = "unsafe_destination"
    except CredentialEncryptionError:
        safe_error_code = "signing_secret_unavailable"
    except httpx.RequestError:
        safe_error_code = "network_error"

    duration_ms = max(0, int((time.monotonic() - started) * 1000))
    attempt = EventDeliveryAttempt(
        outbox_event_id=event.id,
        attempt_number=attempt_number,
        outcome=outcome,
        http_status=http_status,
        safe_error_code=safe_error_code,
        duration_ms=duration_ms,
        attempted_at=datetime.now(timezone.utc),
    )
    session.add(attempt)
    now = datetime.now(timezone.utc)
    if outcome == "delivered":
        event.delivery_status = "delivered"
        event.delivered_at = now
        event.last_error_code = None
        event.next_attempt_at = now
    elif safe_error_code == "unsafe_destination" or attempt_number >= _MAX_ATTEMPTS:
        event.delivery_status = "dead_letter"
        event.last_error_code = safe_error_code or "max_attempts_exceeded"
        event.next_attempt_at = now
    else:
        event.delivery_status = "retry"
        event.last_error_code = safe_error_code or "delivery_failed"
        delay_seconds = min(5 * (2 ** (attempt_number - 1)), 21600)
        event.next_attempt_at = now + timedelta(seconds=delay_seconds)
    session.add(event)
    await session.commit()
    if outcome == "delivered":
        logger.info("Delivered NetPay event {}", event.event_id)
    else:
        logger.warning("NetPay event {} delivery outcome: {}", event.event_id, event.last_error_code)


async def dispatch_outbox_once(
    session: AsyncSession,
    transport: httpx.AsyncBaseTransport | None = None,
    batch_size: int = _BATCH_SIZE,
) -> int:
    """Claim due outbox events and deliver them with retries and stable IDs."""
    now = datetime.now(timezone.utc)
    result = await session.exec(
        select(EventOutbox)
        .where(
            EventOutbox.delivery_status.in_(["pending", "retry", "delivering"]),
            EventOutbox.next_attempt_at <= now,
        )
        .order_by(EventOutbox.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    events = list(result.all())
    for event in events:
        event.attempts += 1
        event.delivery_status = "delivering"
        event.next_attempt_at = now + _DELIVERY_LEASE
        session.add(event)
    await session.commit()

    delivered_for_processing = 0
    for event in events:
        destination_result = await session.exec(
            select(EventDestination).where(
                EventDestination.merchant_id == event.merchant_id,
                EventDestination.enabled.is_(True),
            )
        )
        destination = destination_result.first()
        if destination is None:
            event.delivery_status = "skipped"
            event.attempts = max(0, event.attempts - 1)
            event.next_attempt_at = datetime.now(timezone.utc)
            session.add(event)
            await session.commit()
            continue
        await _deliver_one(session, event, destination, transport)
        delivered_for_processing += 1
    return delivered_for_processing


async def run_worker() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Starting NetPay durable event worker")
    try:
        while True:
            try:
                async with session_factory() as session:
                    await recover_stale_submissions(session)
                    await reconcile_unmatched_callbacks(session)
                    await dispatch_outbox_once(session)
            except Exception as exc:
                # Avoid logging provider payloads, destination URLs or credentials.
                logger.error("NetPay worker iteration failed: {}", type(exc).__name__)
            await asyncio.sleep(2)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
