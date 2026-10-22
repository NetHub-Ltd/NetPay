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
