# NetPay backend

Fresh FastAPI service using PostgreSQL as durable storage, SQLModel for typed persistence, Alembic for versioned schema changes, and Redis for auxiliary caching/coordination. This phase does not restore legacy backend code.

## Local development

1. Start PostgreSQL and Redis locally.
2. Copy `.env.example` to `.env` and adjust local-only values.
3. Install, migrate, and run:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

PostgreSQL is required at startup. Redis is auxiliary: an unavailable Redis instance is logged and reported by readiness but does not block startup. Payment correctness must never rely on Redis durability.

## Database contract

- Configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DB_SSL_MODE` separately. Settings construct `postgresql+asyncpg` for runtime and `postgresql+psycopg` for Alembic with SQLAlchemy's URL builder.
- For Aiven, set `DB_SSL_MODE=require` (or the stronger verification mode appropriate to the configured CA). Local CI explicitly disables SSL for its local PostgreSQL service.
- Generated connection URLs contain credentials and must never be logged.
- The migration environment lives under `alembic/`; `alembic.ini` uses `script_location = alembic`.
- The default pool keeps at most one connection per process and permits no overflow. Pool size, overflow, timeout, and recycle are configurable via `DB_POOL_*` settings. Each worker/process and each Render instance owns its own pool, so total PostgreSQL connections equal the sum of all process pools.
- A pool size of one still retains one idle connection after the first use. Use `NullPool` only if avoiding retained idle connections is more important than the extra connection setup cost.
- Datetimes use timezone-aware UTC values and PostgreSQL `TIMESTAMPTZ` columns.
- Money is stored as integer minor units plus currency code.
- The 16-table schema covers merchants, Daraja integrations, M2M clients, payments/attempts, idempotency, provider requests/callbacks/verification, reconciliation runs/items, outbox events, webhook endpoints, deliveries/attempts, and audit events.
- Constraints enforce unique merchant references, idempotency keys, provider callback fingerprints, stable outbox event IDs, positive payment amounts, valid reconciliation windows, and nonnegative retry counts.
- `deleted_at` is the sole soft-delete marker.
- Never edit an applied migration; add a new revision for later schema changes. The full domain schema is revision `0002_full_domain_schema`.

## Health

- `GET /health/live`: process liveness.
- `GET /health/ready`: PostgreSQL required; Redis status reported separately.
- `GET /docs`: OpenAPI docs.

## Tests

```bash
pytest -q smoke_tests
```

## M-Pesa Core

The internal app.mpesa_core package is the only supported boundary for Daraja transport, OAuth, typed provider operations, credential resolution, and provider-operation audit. Application modules should call MpesaCore; they should not build provider URLs/headers or parse raw Daraja responses. The Core does not own NetPay's canonical payment state or ledger effects.

Required configuration for using the Core:
- MPESA_CREDENTIAL_ENCRYPTION_KEYS: comma-separated key-id=Fernet-key entries supplied by secret management. Keep old key IDs present during rotation until stored credentials are re-encrypted.
- MPESA_CREDENTIAL_ACTIVE_KEY_ID: key ID used for new ciphertext.
- MPESA_PUBLIC_BASE_URL: public callback origin; production must be HTTPS.
- MPESA_HTTP_TIMEOUT_SECONDS: bounded provider timeout.
- MPESA_SANDBOX_CERTIFICATE_PEM / MPESA_PRODUCTION_CERTIFICATE_PEM: public Safaricom certificates for API-initiator operations such as B2C/B2B, status, balance and reversal.

The providerintegration.enabled_capabilities allowlist defaults to stk_push. Enable additional capabilities only after confirming the merchant's product, shortcode, API user, initiator/security credential, and Daraja permissions. C2B URL registration is opt-in and requires c2b_enabled plus the c2b_registration capability. External C2B validation is separately gated by c2b_validation; the current handler does not implement merchant-specific account-reference rules.

Operation results describe provider interaction, not financial settlement. accepted means the provider accepted a request for processing; unknown means the request outcome cannot safely be determined; not_sent means a connection could not be established before the request was sent. Do not automatically retry unknown STK, registration, disbursement, or reversal outcomes.

Callback routes:
- POST /callbacks/mpesa/stk/{integration_id}
- POST /callbacks/mpesa/c2b/validation/{integration_id}
- POST /callbacks/mpesa/c2b/confirmation/{integration_id}
- Asynchronous result routes under /callbacks/mpesa/{operation}/{integration_id}

Callbacks are untrusted evidence, are stored with minimized payloads and deduplicated, and do not directly mutate canonical payment state. The payment domain remains responsible for guarded state transitions and financial effects.

Core tests live in smoke_tests/test_mpesa_core.py. Run with the existing PostgreSQL/Redis-backed CI workflow after applying alembic upgrade head.
