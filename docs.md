# docs.md — NetHub Payment Gateway

## Bootstrap

1. Alembic `upgrade head` (sync URL from `DATABASE_URL`)
2. Probe DB — fatal in production if down
3. Probe Redis — fatal when `REDIS_REQUIRED=true` or production
4. Ensure admin from `ADMIN_EMAIL` / `ADMIN_PASSWORD`

## Dual DB URLs

| Async | Sync |
|-------|------|
| `sqlite+aiosqlite://…` | `sqlite://…` |
| `postgresql+asyncpg://…` | `postgresql://…` |

## M-Pesa

OAuth (Redis-cached), STK Push, C2B RegisterURL. Sandbox: `sandbox.safaricom.co.ke`.

## Webhooks

HTTPS only, HMAC-SHA256 (`X-Nethub-Signature`), max 3/tenant, liveness probe before save.

## STK path

Intent → STK with tenant creds → store `CheckoutRequestID` → Worker envelope → match → status + fanout.

## Routes

| Path | Auth |
|------|------|
| `GET /health` | public |
| `POST /auth/login` | public |
| `/v1/tenants` | admin |
| `/v1/integrations` | admin/tenant |
| `/v1/webhooks` | admin/tenant |
| `/v1/payment-intents` | admin/tenant |
| `/v1/events` | admin/tenant |
| `POST /internal/events` | X-Internal-Api-Key |

## Auth model

**NetPay does not own user registration or login.** Users authenticate via **NetHub AS** and present a bearer token. See [docs/auth-model.md](docs/auth-model.md).

Local password login remains transitional for development until AS token validation is enabled.


## Redis (production)

| Env | Meaning |
|-----|---------|
| `REDIS_URL` | Redis connection URL |
| `REDIS_REQUIRED` | `true` in production / multi-replica |

**Uses today (not a general cache):**

1. Daraja OAuth access-token cache (TTL ≈ expires_in − 60s)
2. Live SPA event pub/sub across API processes
3. Shared rate limits for `POST /v1/oauth/token` and `POST /v1/payment-intents`

When `REDIS_REQUIRED=true` or `ENVIRONMENT=production`:

- Boot fails if Redis is unreachable
- `/health` is not `ok` without Redis
- Rate limiting does **not** fall back to per-process memory (returns 503 `rate_limit_unavailable`)

Financial state (intents, ledger, idempotency, webhooks) stays in Postgres only.
