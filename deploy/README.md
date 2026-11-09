# NetPay deployment notes

## Architecture (binding)

| Item | Contract |
|------|----------|
| Image | Single multi-stage image: Next.js static export copied into FastAPI `STATIC_DIR` (`/app/static`) |
| Registry | `ghcr.io/nethub-ltd/netpay` (tags from **release on `main` only**) |
| Integration branch | `dev` — all feature PRs target `dev` |
| Production promote | Merge `dev` → `main` only after acceptance; release workflow tags + pushes GHCR |
| Runtime | k3s preferred: one-shot **migrate Job**, then **API Deployment** (replicas) + **worker Deployment** |
| Deploy apply | **Flux / human operators** own cluster apply. Agents must not apply Flux changes without explicit approval |
| Data | PostgreSQL is authoritative for payments, membership, outbox. Redis is auxiliary |

API routes, OIDC callback pages, and Daraja callback routes share the **same public origin** when the SPA is served by FastAPI.

## Docker Compose (local)

1. Copy `backend/.env.example` to `backend/.env` and set required secrets (see inventory below).
2. Set `MPESA_PUBLIC_BASE_URL` to a publicly reachable HTTPS origin for Daraja callbacks (use a secure tunnel for local sandbox; not `localhost` for real callbacks).
3. From repository root:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Compose waits for PostgreSQL, runs the one-shot Alembic migration service, then starts the API (and worker when configured).

## Kubernetes (k3s)

### Secret: `nethub-gateway-secrets`

Canonical names match `backend/app/core/config.py` / `backend/.env.example`. **Do not invent alternate names.**

#### Required for core API / payments

| Key | Purpose |
|-----|---------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSL_MODE` | PostgreSQL; use `DB_SSL_MODE=require` for managed TLS (e.g. Aiven). App builds asyncpg/psycopg URLs internally |
| `M2M_TOKEN_SIGNING_SECRET` | Signs NetPay M2M access tokens (long random; secret manager) |
| `MPESA_CREDENTIAL_ENCRYPTION_KEYS` | Fernet key map for Daraja credential encryption |
| `MPESA_CREDENTIAL_ACTIVE_KEY_ID` | Active key id (e.g. `v1`) |
| `MPESA_PUBLIC_BASE_URL` | Public HTTPS origin for `/callbacks/mpesa/*` (must be reachable by Safaricom) |

#### Optional / auxiliary

| Key | Purpose |
|-----|---------|
| `REDIS_URL` | Redis URL (`redis://` / `rediss://`) |
| `REDIS_ENABLED` | `true` / `false` — Redis is auxiliary; readiness reports it but must not fail the process solely for identity |
| `ENVIRONMENT` | `development` \| `test` \| `staging` \| `production` |
| `LOG_LEVEL` | Log level |

#### Human identity (NetHubKe client) — required for dashboard OIDC

| Key | Purpose |
|-----|---------|
| `NETHUB_API_BASE_URL` | NetHubKe API origin (no trailing slash required; stripped in code) |
| `NETHUB_API_TIMEOUT_SECONDS` | Upstream timeout (default `8`, max `60`) |
| `OIDC_ISSUER` | IdP issuer URL (appears in public `/config.json`) |
| `OIDC_CLIENT_ID` | **Public** SPA client id — must be registered in NetHubKe `trusted_clients` |
| `OIDC_REDIRECT_URI` | Exact redirect, e.g. `https://pay.example.com/auth/callback/` (trailing slash must match Next + IdP app) |
| `OIDC_SCOPES` | Default without refresh until I7: `openid profile email` (see issue #235) |

Also set frontend build-time `NEXT_PUBLIC_SITE_URL` when building images for non-default public origin (canonical URLs, sitemap, metadata).

**Fail-closed human auth:** If `NETHUB_API_BASE_URL` or OIDC fields are empty, human `/api/v1/auth/*` fails as designed; **M2M payments, callbacks, public static pages, and health probes must still work.**

> Legacy notes sometimes mentioned `SECRET_KEY`, `CREDENTIAL_ENCRYPTION_KEY`, `PUBLIC_BASE_URL`, or `CORS_ORIGINS`. Prefer the canonical table above. If an old cluster secret still uses legacy names, map them explicitly in the operator runbook — do not assume silent aliases in application code.

### Rollout order

```bash
# 1. Ensure nethub-gateway-secrets contains required keys (including identity keys for staging dashboard)
# 2. Migrate once per release image
kubectl delete job nethub-gateway-migrate --ignore-not-found
kubectl apply -f deploy/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/nethub-gateway-migrate --timeout=180s
# 3. Roll API + worker
kubectl apply -f deploy/k8s/deployment.yaml
```

### Probes

| Probe | Path | Contract |
|-------|------|----------|
| Liveness | `GET /health/live` | Process up; **no** dependency calls |
| Readiness | `GET /health/ready` | **PostgreSQL required**; Redis reported as auxiliary (`ok` / `unavailable` / `disabled`) |

**Readiness must not call NetHubKe or IdP.** Identity outage removes human login capability, not pod readiness.

### Worker

Worker uses PostgreSQL row locking and durable retry timestamps; deploy separately from API replicas (`python -m app.worker`).

## Identity + dashboard status

- Human identity: IdP access token → NetPay forwards Bearer to **NetHubKe resource server** → local `merchant_member` ACL. See `docs/identity-nethub-rs.md`.
- Dashboard serves OIDC PKCE shell (profile + memberships). **Do not expose merchant payment data in the UI until membership-gated APIs and staging E2E (issues #236–#238) pass.**
- M2M API and Daraja callback pipeline remain the machine integration surface.

## Important boundaries

- Do **not** merge rebuild identity work to `main` / trigger GHCR release until program gates (through I6) and explicit approval.
- Do **not** put production client IDs, tokens, or admin emails in git.
- Flux owns production reconciliation; this folder is the in-repo contract reference.
