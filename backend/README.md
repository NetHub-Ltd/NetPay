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

PostgreSQL is the source of truth for payments, idempotency, callback deduplication, and the transactional event outbox. Redis is auxiliary and must not be required for correctness.

## Current implementation boundary

The initial API/runtime foundation, credential encryption primitive, and first SQLModel schema are in place. Payment initiation, merchant authentication, callback state transitions, and event delivery are implemented in subsequent vertical slices; do not treat this foundation commit as a production-ready payment gateway.
