# NetPay backend

Minimal FastAPI service for the clean backend restart. This stage deliberately contains no database, cache, payment-provider, authentication, or legacy compatibility implementation. Those components will be designed and introduced in separate reviewed steps.

## Local development

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev]"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Copy `.env.example` to `.env` for documented local configuration. The initial bootstrap does not consume environment variables yet.

## Health checks

- `GET /health/live` — process liveness.
- `GET /health/ready` — initial process readiness. Database and other dependency checks are intentionally deferred to the next stage.
- `GET /docs` — generated OpenAPI documentation.

## Tests

    pytest -q smoke_tests/test_startup.py
