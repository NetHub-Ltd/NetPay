"""Documented per-intent callback signature must be verifiable by partners."""
from __future__ import annotations

import hashlib
import hmac
from uuid import uuid4

from app.core.config import settings
from app.services.webhooks import sign_payload


def test_per_intent_secret_derivation_matches_docs():
    intent_id = uuid4()
    secret = hashlib.sha256(f"{settings.secret_key}:{intent_id}".encode()).hexdigest()
    body = '{"event":"payment.update","status":"succeeded"}'
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    assert sign_payload(secret, body) == expected
