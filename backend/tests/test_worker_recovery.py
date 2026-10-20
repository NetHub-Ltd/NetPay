from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlmodel import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session

from app.config import get_settings
from app.crypto import encrypt_secret
from app.models import DarajaIntegration, EventOutbox, Merchant, Payment, PaymentAttempt
from app.worker import recover_stale_submissions


def _sync_url() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)


@pytest.mark.asyncio
async def test_stale_submitting_payment_becomes_unknown_without_retry() -> None:
    engine = create_engine(_sync_url())
    settings = get_settings()
    now = datetime.now(timezone.utc)
    old = now - timedelta(minutes=4)
    merchant = Merchant(name=f"Recovery merchant {uuid4()}", status="active", created_at=old, updated_at=old)
    integration_id = f"int_{uuid4().hex}"
    integration = DarajaIntegration(
        integration_id=integration_id,
        merchant_id=merchant.id,
        environment="sandbox",
        shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        consumer_key_ciphertext=encrypt_secret("consumer-key", settings),
        consumer_secret_ciphertext=encrypt_secret("consumer-secret", settings),
        passkey_ciphertext=encrypt_secret("passkey", settings),
        credential_status="oauth_validated",
        c2b_enabled=False,
        c2b_registration_status="not_requested",
        stk_callback_url=f"https://gateway.example.test/cb/stk/{integration_id}",
        c2b_validation_url=f"https://gateway.example.test/cb/c2b/validation/{integration_id}",
        c2b_confirmation_url=f"https://gateway.example.test/cb/c2b/confirmation/{integration_id}",
        created_at=old,
        updated_at=old,
    )
    payment = Payment(
        merchant_id=merchant.id,
        integration_id=integration.id,
        client_reference=f"recovery-{uuid4().hex[:12]}",
        amount_minor=100,
        currency="KES",
        phone_number="254712345678",
        status="pending",
        created_at=old,
        updated_at=old,
    )
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=1,
        outcome="submitting",
        created_at=old,
        updated_at=old,
    )
    payment_id = payment.id
    attempt_id = attempt.id
    with Session(engine) as session:
        session.add(merchant)
        session.add(integration)
        session.add(payment)
        session.add(attempt)
        session.commit()
    engine.dispose()

    async_engine = create_async_engine(get_settings().database_url)
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            recovered = await recover_stale_submissions(session)
    finally:
        await async_engine.dispose()

    assert recovered == 1
    engine = create_engine(_sync_url())
    with Session(engine) as session:
        saved_payment = session.exec(select(Payment).where(Payment.id == payment_id)).one()
        saved_attempt = session.exec(select(PaymentAttempt).where(PaymentAttempt.id == attempt_id)).one()
        events = session.exec(select(EventOutbox).where(EventOutbox.aggregate_id == payment_id)).all()
    engine.dispose()
    assert saved_payment.status == "unknown"
    assert saved_attempt.outcome == "unknown"
    assert saved_attempt.safe_error_code == "worker_recovered_stale_submission"
    assert len(events) == 1
    assert events[0].event_type == "payment.unknown"
