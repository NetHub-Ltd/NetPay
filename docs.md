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
