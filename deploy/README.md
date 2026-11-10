# NetPay deployment

## Runtime architecture

NetPay is deployed as two independent application services:

| Service | Image | Runtime | Responsibility |
|---|---|---|---|
| Next.js frontend | ghcr.io/nethub-ltd/netpay-frontend | Node.js 22 / Next standalone | Public pages, login, dashboard, OIDC callback and HTTP BFF |
| FastAPI API | ghcr.io/nethub-ltd/netpay | Python 3.12 / Uvicorn | M2M APIs, payments, merchant authorization, callbacks and encrypted BFF session persistence |
| Worker | Same FastAPI image | Python | Durable event and payment work |
| PostgreSQL | Managed / PostgreSQL 16 | Database | Financial source of truth and BFF session store |
| Redis | Optional auxiliary | Cache/coordination | Never the source of truth |

The browser communicates with the Next.js origin only for the NetPay application. Authenticated HTTP API requests use same-origin Next.js Route Handlers under /api/backend/*. The Next.js server calls FastAPI using the private NETPAY_BACKEND_INTERNAL_URL. Upstream OIDC tokens are encrypted at rest in the bffsession table and never exposed to browser JavaScript.

FastAPI continues to enforce merchant membership, tenant isolation and business authorization. M2M clients and Safaricom continue using the existing API and callback contracts.

## Build images

Run from the repository root:

    docker build -f backend/Dockerfile -t ghcr.io/nethub-ltd/netpay:local .
    docker build -f frontend/Dockerfile -t ghcr.io/nethub-ltd/netpay-frontend:local .

The API image no longer contains Node.js or frontend assets. The Next.js image uses standalone output and runs node server.js. Both images run as non-root users.

## Environment variables

### FastAPI API and worker

Continue configuring the existing DB_*, DATABASE_URL, REDIS_*, NETHUB_API_*, M2M_TOKEN_SIGNING_SECRET and MPESA_* settings. Add:

| Variable | Purpose |
|---|---|
| BFF_INTERNAL_SECRET | High-entropy shared service credential used only by Next.js to access /internal/v1/bff/sessions |
| BFF_SESSION_ENCRYPTION_KEY | Dedicated Fernet key used to encrypt OIDC access/refresh tokens at rest |

Generate a separate encryption key:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Do not reuse Daraja credential keys, database passwords or the BFF internal secret.

### Next.js frontend

| Variable | Purpose |
|---|---|
| NETPAY_BACKEND_INTERNAL_URL | Private/internal FastAPI origin; never a NEXT_PUBLIC_ variable |
| BFF_INTERNAL_SECRET | Same value as the API's BFF_INTERNAL_SECRET |
| OIDC_ISSUER | Zitadel issuer URL |
| OIDC_CLIENT_ID | Confidential server-side NetPay web client ID |
| OIDC_CLIENT_SECRET | Confidential web client secret; frontend server only |
| OIDC_REDIRECT_URI | Exact public callback URL, normally https://<frontend-origin>/auth/callback/ |
| OIDC_SCOPES | At minimum openid profile email; request offline_access only when enabled for the registered client |
| OIDC_TRANSACTION_SECRET | Independent random secret of at least 32 characters for encrypted short-lived PKCE transaction cookies |
| NEXT_PUBLIC_SITE_URL | Public canonical frontend origin for SEO metadata only |

Never pass OIDC_CLIENT_SECRET, BFF_INTERNAL_SECRET or OIDC_TRANSACTION_SECRET as build arguments. Configure them at runtime through the platform's secret manager.

## Database migration

Run migrations once before starting new API replicas:

    cd backend
    alembic upgrade head

Migration 0005 adds the BFF session table. Session handles are stored as SHA-256 hashes; upstream access and refresh tokens are encrypted with BFF_SESSION_ENCRYPTION_KEY. Keep the database backup and migration rollback plan consistent with the normal NetPay database process.

## Local Compose

1. Copy backend/.env.example to backend/.env and set local DB values.
2. Copy frontend/.env.example to frontend/.env.local.
3. Generate BFF_INTERNAL_SECRET and BFF_SESSION_ENCRYPTION_KEY; set the BFF internal secret identically in both services.
4. Register a confidential OIDC web client with redirect URI http://localhost:3000/auth/callback/.
5. Run:

    docker compose -f deploy/docker-compose.yml up --build

Frontend: http://localhost:3000  
FastAPI API: http://localhost:8000  
OpenAPI: http://localhost:8000/docs

## Render staging

Keep the existing Render service as the FastAPI API service so its public API and Safaricom callback base URL remain stable. Deploy a second Render web service from frontend/Dockerfile for Next.js.

Configure:
- API service: existing database, NETHUB_API_BASE_URL, MPESA_PUBLIC_BASE_URL, BFF_INTERNAL_SECRET and BFF_SESSION_ENCRYPTION_KEY.
- Frontend service: OIDC_* settings, OIDC_TRANSACTION_SECRET, BFF_INTERNAL_SECRET (same value), NETPAY_BACKEND_INTERNAL_URL set to the API's private service URL, and NEXT_PUBLIC_SITE_URL set to the frontend's public origin.
- Register the frontend origin and exact /auth/callback/ redirect URI in Zitadel and NetHubKe trusted-client/CORS configuration as required by the existing NetHubKe contract.
- Ensure both services use the same PostgreSQL database and the API migration has run before frontend sign-in is tested.
- Keep Safaricom callback URLs pointing to the API service origin unless ingress is configured to route /callbacks/mpesa to FastAPI.

Render service names, private hostnames and domain bindings are operator-controlled; do not guess them in committed configuration. The frontend's browser-facing API remains same-origin because the browser calls the frontend BFF, not the API service hostname.

## Kubernetes ingress and WSS

The manifest deploys Next.js and FastAPI separately. Ingress routes / to Next.js, /api/v1 and /callbacks/mpesa to FastAPI for M2M and provider traffic. The /internal/* session-store routes are not routed publicly. Set the same BFF_INTERNAL_SECRET in both Kubernetes secrets.

The ingress controller must support HTTP/1.1 WebSocket upgrades. No dedicated WebSocket endpoint or gateway is deployed by this change because the current NetPay product has no concrete WebSocket use case. When one is introduced, reserve /ws/* and route it to a dedicated authenticated realtime service; authenticate the application session or a short-lived scoped credential and authorize every subscription against merchant membership. Do not use ordinary Next.js Route Handlers as a WebSocket proxy.

## Health and rollback

- FastAPI liveness: /health/live
- FastAPI readiness: /health/ready (PostgreSQL required; Redis remains auxiliary)
- Next.js liveness: /login/
- Next.js readiness: /api/auth/status (reports only non-secret configuration booleans)

Deploy database migrations before the API image. Deploy the API and Next.js images as a compatible pair. Rollback both service images together if a release changes their internal session contract; never roll back the database migration without checking whether active sessions or newer API code depend on it.
