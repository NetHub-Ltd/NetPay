# NetPay backend

FastAPI service for the multi-merchant M-Pesa Daraja gateway.

## Local development

Run from this directory:

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

The API exposes OpenAPI docs at `/docs`, process liveness at `/health/live`, and dependency readiness at `/health/ready`. The compatibility `/health` endpoint remains for existing deployment probes.

Set `DATABASE_URL` to PostgreSQL for integration and production work. SQLite is intended for isolated unit tests. Production requires a non-default `SECRET_KEY` and a valid Fernet `CREDENTIAL_ENCRYPTION_KEY`; generate the latter with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Apply schema changes explicitly before starting the application:

```bash
uv run alembic upgrade head
```

PostgreSQL is the source of truth for payments, idempotency, callback deduplication, delivery attempts, and the transactional event outbox. The current worker uses PostgreSQL row locking and retry timestamps; Redis is deliberately omitted until a measurable coordination or caching need justifies it.

## Current implementation boundary

The initial API/runtime foundation, credential encryption primitive, and first SQLModel schema are in place. Payment initiation, merchant authentication, callback state transitions, and event delivery are implemented in subsequent vertical slices; do not treat this foundation commit as a production-ready payment gateway.

## M2M client bootstrap

After migrations, provision the first merchant/client from a trusted operator environment:

```bash
MERCHANT_NAME="Example Merchant" uv run python -m scripts.provision_m2m_client
```

The command creates a merchant, stores only a scrypt hash of the generated client secret, and prints the client secret once. Transfer it to a secret manager immediately. The default scopes are `integrations:read`, `integrations:write`, `payments:read`, `payments:write`, `events:read`, and `events:write`; override them with `NETPAY_CLIENT_SCOPES` if needed.

Exchange the client ID and secret for a short-lived bearer token:

```bash
curl -u "$NETPAY_CLIENT_ID:$NETPAY_CLIENT_SECRET" \
  -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "grant_type=client_credentials"
```

Use the returned access token as `Authorization: Bearer <token>`. Tokens expire after 15 minutes. Integration onboarding validates the Daraja OAuth consumer key/secret; it does not prove the shortcode permissions or passkey are valid. C2B URL registration remains opt-in.

## Webhook delivery worker

Run a separate worker process alongside the API:

```bash
uv run python -m app.worker
```

The worker recovers callbacks that arrived before STK correlation IDs were committed and drains the PostgreSQL outbox. No Redis or external broker is required for correctness. Configure one optional destination per merchant with `PUT /api/v1/event-destination` using the `events:write` scope. The response contains a newly generated signing secret once; save it immediately because the stored value is encrypted and cannot be retrieved. Repeating PUT rotates the signing secret.

Webhook requests include `X-NetPay-Event-Id`, `Idempotency-Key`, and `X-NetPay-Signature: sha256=<hex>`. The signature is HMAC-SHA256 over the exact request body. Consumers should verify the signature and deduplicate by event ID. Failed deliveries retry with exponential backoff and eventually enter a dead-letter state; delivery attempts are retained in PostgreSQL.

The public dashboard currently has a no-index entry screen only. Merchant sign-in/session integration is not yet wired; no merchant data is exposed by that page.
