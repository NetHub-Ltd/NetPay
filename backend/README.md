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


## Provider credential encryption and machine authentication

- Set `CREDENTIAL_ENCRYPTION_KEY` to a Fernet key generated with the command in `.env.example`. Keep it in the deployment secret store, separate from PostgreSQL, and preserve it across releases. The application does not generate a fallback key. Missing or invalid configuration fails closed when credential encryption is requested.
- Set a unique random `SECRET_KEY` of at least 32 bytes in production. The checked-in value is only for local development and is rejected for production token signing.
- `MACHINE_TOKEN_TTL_MINUTES` defaults to 60 and is bounded to 1–1440 minutes. `MACHINE_TOKEN_AUDIENCE` defaults to `netpay`.
- Provider credentials must be encrypted before assigning ciphertext columns. Decrypt only at the provider-call boundary; never log plaintext or return it in API responses.
- M2M client secrets are generated and hashed before persistence. The `/v1/oauth/token` endpoint exchanges a stored client ID/secret for a short-lived bearer token. The `/v1/oauth/me` endpoint demonstrates the authenticated principal and returns no secrets. Client provisioning must remain an authenticated operator workflow; there is no anonymous client-creation endpoint.
- Each authenticated M2M request re-checks the persisted client and merchant status, expiry, revocation, and granted scopes so disabling a client takes effect immediately. Derive tenant IDs from the verified principal rather than request-body merchant IDs.


### Initial M2M client provisioning

- An operator may create a client for an already-existing active merchant with `POST /v1/internal/m2m-clients` and the `X-NetPay-Provisioning-Key` header. Configure `M2M_PROVISIONING_KEY` as a random secret of at least 32 bytes; the endpoint returns 404 when it is not configured or is too short.
- The request accepts only the declared integration/payment/event scopes and an optional timezone-aware expiry. The generated client secret is returned once; only its PBKDF2 hash is persisted. There is no client-list or secret-read endpoint.
- Keep this key in the deployment secret store and do not put it in a browser, source control, query string, or logs. This bootstrap route is an operator-only bridge until a fully authenticated operator workflow is implemented.


## Daraja integration onboarding

- A merchant M2M client with `integrations:write` can create an integration through `POST /v1/integrations`; the merchant ID is derived from the verified bearer token, not accepted from the request body. `integrations:read` clients can list or inspect only their own integrations.
- The create request validates the consumer key/secret against the official Daraja Authorization API for the selected environment, then stores the consumer key, consumer secret, and passkey as authenticated ciphertext. OAuth validation proves the app credentials can obtain a token; it does not prove every shortcode/product permission or passkey is valid.
- Set `PUBLIC_API_BASE_URL` to the public NetPay origin used for callback generation. Production integrations require HTTPS. STK and C2B callback URLs are generated and persisted automatically; this phase does not register C2B URLs or implement callback processing.
- The integration response intentionally excludes credential plaintext and ciphertext. Invalid credentials are not saved as active integrations. Provider calls use `DARAJA_TIMEOUT_SECONDS` and return sanitized errors.


## STK Push and callback safety

- `POST /v1/payments` requires a merchant-scoped `payments:write` bearer token and an `Idempotency-Key`. It persists the payment, attempt, provider request, and idempotency record before contacting Daraja. A replay with the same key and request returns the existing payment; a changed request with the same key is rejected.
- Amounts are accepted as whole KES and stored as integer minor units (KES × 100). Kenyan mobile numbers are normalized to the `2547...` or `2541...` form. Each STK request uses the integration's encrypted credentials, passkey, shortcode, product type and generated callback URL.
- An STK acceptance response leaves the payment pending; it is not proof of payment. A timeout or ambiguous provider response leaves the payment `unknown` and is never retried automatically.
- `POST /v1/callbacks/stk/{integration_id}` stores only allow-listed callback evidence and deduplicates by provider request ID/fingerprint. Callback bodies are untrusted: even a callback with result code zero cannot mark a payment successful. Matched callbacks move non-terminal payments to `unknown` pending provider-authoritative verification; mismatches and conflicts remain for reconciliation. This slice does not yet implement STK query verification or outbox event publication.
- Daraja request format is based on the official [M-Pesa Express documentation](https://developer.safaricom.co.ke/apis/MpesaExpressSimulate). The [Authorization API](https://developer.safaricom.co.ke/apis/Authorization) issues the short-lived OAuth token used for provider requests.


### Daraja access-token cache

- STK initiation reuses an encrypted access-token cache stored in PostgreSQL on the integration record and refreshes it before expiry. A row lock serializes refreshes for the same integration; tokens are never logged or returned to API clients.
- Safaricom's [Authorization API documentation](https://developer.safaricom.co.ke/apis/Authorization) describes the OAuth client-credentials flow and token expiry. Treat each integration as owning its own Daraja app credentials; do not share one Daraja app credential set across unrelated merchants. A future shared-credential deployment would need a cache keyed by credential fingerprint across integrations.
- Alembic revision `0003_provider_token_cache` adds the encrypted token and expiry fields without changing prior revision IDs.
