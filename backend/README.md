# NetPay FastAPI backend

FastAPI is an independently deployed API service. It does not build or serve frontend files. PostgreSQL is durable storage; SQLModel provides typed persistence, Alembic manages schema changes and Redis remains auxiliary.

## Local development

1. Start PostgreSQL and Redis locally.
2. Copy .env.example to .env and configure local-only values.
3. Install, migrate and run:

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev]"
    alembic upgrade head
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

PostgreSQL is required at startup. Redis is auxiliary: an unavailable Redis instance is logged and reported by readiness but does not block startup. Payment correctness must never rely on Redis durability.

## Database contract

- Configure DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD and DB_SSL_MODE separately.
- For Aiven, set DB_SSL_MODE=require (or the stronger verification mode appropriate to the configured CA).
- Generated connection URLs contain credentials and must never be logged.
- The migration environment lives under alembic/; alembic.ini uses script_location = alembic.
- The default pool keeps at most one connection per process and permits no overflow. Pool size, overflow, timeout and recycle are configurable.
- Datetimes use timezone-aware UTC values and PostgreSQL TIMESTAMPTZ columns.
- Money is stored as integer minor units plus currency code.
- Never edit an applied migration; add a new revision for later schema changes. Revision 0005 adds the BFF session store.

## BFF session persistence

The Next.js server uses the private NETPAY_BACKEND_INTERNAL_URL to access internal session-store routes under /internal/v1/bff/sessions. These routes:
- Require X-NetPay-BFF-Secret and are excluded from OpenAPI.
- Store only a SHA-256 hash of the opaque browser session handle.
- Encrypt upstream access/refresh tokens using BFF_SESSION_ENCRYPTION_KEY.
- Use an optimistic version to prevent concurrent refresh-token rotations from overwriting each other.
- Must not be exposed through the FastAPI public ingress. The Next.js application is hosted independently on Vercel; `NETPAY_BACKEND_INTERNAL_URL` must point to an origin reachable from the Vercel server runtime. Do not assume a cluster-only hostname is reachable from Vercel. If the platform exposes internal routes on a public service hostname, the high-entropy shared secret remains mandatory and platform-level path filtering/network controls should be applied where supported.
- Never expose the internal secret or encryption key to browser code.

BFF_INTERNAL_SECRET is a high-entropy shared service credential. BFF_SESSION_ENCRYPTION_KEY is a dedicated Fernet key and must not be reused for Daraja credentials.

## Health and API boundaries

- GET /health/live: process liveness.
- GET /health/ready: PostgreSQL required; Redis status reported separately.
- GET /docs: OpenAPI docs.
- FastAPI owns M2M APIs and Safaricom callbacks. The browser application must not call FastAPI directly; it uses the Next.js BFF.
- Direct human API calls without a valid Bearer token are rejected. Merchant membership and business authorization remain enforced by FastAPI.

## Tests

    pytest -q tests

Run alembic upgrade head against the test database before the full suite. CI verifies PostgreSQL/Redis, migrations, API startup and backend behavior.

## M-Pesa Core

The internal app.mpesa_core package is the only supported boundary for Daraja transport, OAuth, typed provider operations, credential resolution and provider-operation audit. Application modules should call MpesaCore; they should not build provider URLs/headers or parse raw Daraja responses. The Core does not own NetPay's canonical payment state or ledger effects.

Required configuration:
- MPESA_CREDENTIAL_ENCRYPTION_KEYS: comma-separated key-id=Fernet-key entries from secret management.
- MPESA_CREDENTIAL_ACTIVE_KEY_ID: key ID used for new ciphertext.
- MPESA_PUBLIC_BASE_URL: public callback origin; production must be HTTPS.
- MPESA_HTTP_TIMEOUT_SECONDS: bounded provider timeout.
- MPESA_SANDBOX_CERTIFICATE_PEM / MPESA_PRODUCTION_CERTIFICATE_PEM: public Safaricom certificates for API-initiator operations.

The providerintegration.enabled_capabilities allowlist defaults to stk_push. Enable additional capabilities only after confirming merchant product, shortcode, API user, initiator/security credential and Daraja permissions. C2B URL registration is opt-in and separately gated from external account validation.

Operation results describe provider interaction, not financial settlement. accepted means the provider accepted a request for processing; unknown means the request outcome cannot safely be determined; not_sent means a connection could not be established before the request was sent. Do not automatically retry unknown STK, registration, disbursement or reversal outcomes.

Callback routes:
- POST /callbacks/mpesa/stk/{integration_id}
- POST /callbacks/mpesa/c2b/{integration_id}/validation
- POST /callbacks/mpesa/c2b/{integration_id}/confirmation

Callbacks are untrusted evidence, stored with minimized payloads and deduplicated. The payment domain remains responsible for guarded state transitions and financial effects.

## Human identity

See [docs/identity-rs-contract.md](../docs/identity-rs-contract.md). Humans are resolved from NetHubKe RS with optional Redis cache.

