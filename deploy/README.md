# NetPay deployment

## Runtime architecture

NetPay is deployed as two independent application services:

| Service | Image | Runtime | Responsibility |
|---|---|---|---|
| Next.js frontend | Vercel project (Root Directory: `frontend`) | Managed Next.js server runtime | Public pages, login, dashboard, OIDC callback and HTTP BFF |
| FastAPI API | ghcr.io/nethub-ltd/netpay | Python 3.12 / Uvicorn | M2M APIs, payments, merchant authorization, callbacks and encrypted BFF session persistence |
| Worker | Same FastAPI image | Python | Durable event and payment work |
| PostgreSQL | Managed / PostgreSQL 16 | Database | Financial source of truth and BFF session store |
| Redis | Optional auxiliary | Cache/coordination | Never the source of truth |

The browser communicates with the Next.js origin only for the NetPay application. Authenticated HTTP API requests use same-origin Next.js Route Handlers under /api/backend/*. The Next.js server calls FastAPI using the private NETPAY_BACKEND_INTERNAL_URL. Upstream OIDC tokens are encrypted at rest in the bffsession table and never exposed to browser JavaScript.

FastAPI continues to enforce merchant membership, tenant isolation and business authorization. M2M clients and Safaricom continue using the existing API and callback contracts.

## Deployment targets

Deploy Next.js independently on Vercel with Root Directory `frontend` and the Next.js framework preset. Keep the normal Next.js server runtime: no static export, standalone container output or frontend Docker image.

Build only the FastAPI image from the repository root:

    docker build -f backend/Dockerfile -t ghcr.io/nethub-ltd/netpay:local .

## Environment variables

### FastAPI API and worker

Continue configuring the existing DB_*, DATABASE_URL, REDIS_*, NETHUB_API_*, M2M_TOKEN_SIGNING_SECRET and MPESA_* settings. Add:

| Variable | Purpose |
|---|---|
| BFF_INTERNAL_SECRET | High-entropy shared service credential (minimum 32 characters) used only by Next.js to access /internal/v1/bff/sessions |
| BFF_SESSION_ENCRYPTION_KEY | Dedicated Fernet key used to encrypt OIDC access/refresh tokens at rest |

Generate a separate encryption key:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Do not reuse Daraja credential keys, database passwords or the BFF internal secret.

### Next.js frontend

| Variable | Purpose |
|---|---|
| NETPAY_BACKEND_INTERNAL_URL | Private/internal FastAPI origin; never a NEXT_PUBLIC_ variable |
| BFF_INTERNAL_SECRET | Same high-entropy value (minimum 32 characters) as the API's BFF_INTERNAL_SECRET |
| OIDC_ISSUER | Zitadel issuer URL |
| OIDC_CLIENT_ID | Public NetPay OIDC client ID; token exchange is bound with PKCE |
| OIDC_REDIRECT_URI | Exact public callback URL, normally https://<frontend-origin>/auth/callback/ |
| OIDC_SCOPES | At minimum openid profile email; request offline_access only when enabled for the registered client |
| OIDC_TRANSACTION_SECRET | Independent random secret of at least 32 characters for encrypted short-lived PKCE transaction cookies |
| NEXT_PUBLIC_SITE_URL | Public canonical frontend origin for SEO metadata only |

Do not pass BFF_INTERNAL_SECRET or OIDC_TRANSACTION_SECRET as build arguments. Configure these application secrets at runtime through the platform's secret manager. Zitadel does not issue a client secret for this public OIDC client.

## Database migration

Run migrations once before starting new API replicas:

    cd backend
    alembic upgrade head

Migration 0005 adds the BFF session table. Session handles are stored as SHA-256 hashes; upstream access and refresh tokens are encrypted with BFF_SESSION_ENCRYPTION_KEY. Keep the database backup and migration rollback plan consistent with the normal NetPay database process.

## Local development

1. Copy backend/.env.example to backend/.env and set local DB values.
2. Copy frontend/.env.example to frontend/.env.local.
3. Generate BFF_INTERNAL_SECRET and BFF_SESSION_ENCRYPTION_KEY; set the BFF internal secret identically in both services.
4. Register a public OIDC client with Authorization Code + PKCE (S256) and redirect URI http://localhost:3000/auth/callback/. No client secret is needed.
5. Start the backend services and dependencies:

    docker compose -f deploy/docker-compose.yml up --build

6. In a separate terminal, run the Next.js development server:

    cd frontend
    npm ci
    npm run dev

Frontend: http://localhost:3000  
FastAPI API: http://localhost:8000  
OpenAPI: http://localhost:8000/docs

Compose intentionally does not build or run a frontend container.

## Vercel and FastAPI configuration

Keep FastAPI on its existing independent runtime. Deploy Next.js independently on Vercel with Root Directory `frontend`.

Configure:
- FastAPI: existing database, NETHUB_API_BASE_URL, MPESA_PUBLIC_BASE_URL, BFF_INTERNAL_SECRET and BFF_SESSION_ENCRYPTION_KEY.
- Vercel: OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_REDIRECT_URI, OIDC_SCOPES, OIDC_TRANSACTION_SECRET, BFF_INTERNAL_SECRET (same value), NETPAY_BACKEND_INTERNAL_URL set to an API origin reachable from the Vercel server runtime, and NEXT_PUBLIC_SITE_URL set to the frontend's public origin.
- Register the exact frontend /auth/callback/ redirect URI in Zitadel and the matching client_id as a NetHubKe trusted client for product netpay. Browser-to-NetHubKe CORS is not required for this server-to-server BFF flow; do not broaden CORS for it.
- Ensure both services use the same PostgreSQL database and the API migration has run before frontend sign-in is tested.
- Keep Safaricom callback URLs pointing to the API service origin unless ingress is configured to route /callbacks/mpesa to FastAPI.

FastAPI service names, private hostnames and domain bindings are operator-controlled; do not guess them in committed configuration. The Vercel server runtime must reach every FastAPI route required by the BFF, including `/internal/v1/bff/sessions/*`, over a service-to-service network path. Keep those session-store routes private to the Vercel/API service channel; the shared BFF secret is mandatory but is not a substitute for network controls. If no private Vercel-to-FastAPI path is available, this remains a staging blocker for the operator to resolve rather than a reason to expose the internal routes broadly. The frontend's browser-facing API remains same-origin because the browser calls the frontend BFF, not the API service hostname.

## API ingress and WSS

Route /api/v1 and /callbacks/mpesa to FastAPI for M2M and provider traffic. Keep /internal/* session-store routes private.

The ingress controller must support HTTP/1.1 WebSocket upgrades. No dedicated WebSocket endpoint or gateway is deployed by this change because the current NetPay product has no concrete WebSocket use case. When one is introduced, reserve /ws/* and route it to a dedicated authenticated realtime service; authenticate the application session or a short-lived scoped credential and authorize every subscription against merchant membership. Do not use ordinary Next.js Route Handlers as a WebSocket proxy.

## Health and rollback

- FastAPI liveness: /health/live
- FastAPI readiness: /health/ready (PostgreSQL required; Redis remains auxiliary)
- Next.js: Vercel-managed runtime; verify `/login/` and the same-origin BFF after deployment.

Deploy database migrations before the API image. Deploy FastAPI independently; Vercel manages frontend builds and rollbacks separately. Keep the BFF contract compatible and never roll back a migration without checking active sessions and API dependencies.
