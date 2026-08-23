# NetHub Payment Gateway v1.1

Multi-tenant M-Pesa orchestration. Clients never talk to Daraja. Cloudflare Worker stays edge-only; this FastAPI service owns auth, intents, provider adapters, webhooks, and events.

## Acceptance checklist

| # | Criterion | Implementation |
|---|-----------|----------------|
| 1 | Env admin → login | `bootstrap.ensure_admin` + `POST /auth/login` |
| 2 | Onboard client + sandbox M-Pesa creds | `POST /v1/tenants`, `POST /v1/integrations` |
| 3 | Register Daraja C2B URLs | `POST /v1/integrations/{id}/register-urls` |
| 4 | ≤3 webhooks after liveness | `POST /v1/webhooks` + probe |
| 5 | STK → callback → status + webhook | `POST /v1/payment-intents` + `POST /internal/events` |
| 6 | Worker path requires internal secret | `X-Internal-Api-Key` on `/internal/*` |
| 7 | Alembic on startup (no create_all) | `startup_sequence` → `alembic upgrade head` |
| 8 | DB + Redis + admin at startup | Health probes; Redis fail-fast when required |

## Quick start

```bash
cp .env.example .env
./run.sh
# http://localhost:8000/docs
```

## Docker / k3s

```bash
docker compose up --build          # local Postgres + Redis
docker build -t nethub/payment-gateway:1.1.0 .
kubectl apply -f k8s/deployment.yaml
```

## Worker contract

```
POST /internal/events
X-Internal-Api-Key: <INTERNAL_API_KEY>
Body: { "event_id", "provider", "event_type", "integration": {"public_id": "gw_…"}, "payload": … }
```

Missing/wrong key → **401**.

## Roles

- `admin` — full access
- `user` — scoped to `tenant_id`

## Tests

```bash
uv run pytest -q
```

## Dashboard (React)

```bash
# development (proxies API to :8000)
cd frontend && npm install && npm run dev

# production static (served by FastAPI)
cd frontend && npm run build
# then start API — UI at http://localhost:8000/
```

Screens: login, health, tenants, integrations (+ Daraja URL register), webhooks, payment intents, event log, OAuth clients. RBAC: admin | user.
