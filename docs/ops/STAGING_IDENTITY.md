# Staging identity — independent Next.js BFF and NetHubKe client

**Related issues:** #233 (operator IdP/NetHubKe registration), #238 (I0–I6 staging acceptance), #239 (mandatory Next.js BFF and server-side identity).
**Rule:** never paste production tokens, client secrets, session cookies or admin credentials into git, issues or chat.

## Service roles

| System | Responsibility |
|---|---|
| Zitadel | User authentication |
| Next.js | Confidential OIDC client, callback, opaque application session, login/dashboard and HTTP BFF |
| FastAPI | API, merchant authorization, payment flows and encrypted BFF session persistence |
| NetHubKe | Human identity resolution and product/resource access decisions |
| Ingress | Public routing to Next.js, M2M API and Safaricom callback paths |

The browser uses the Next.js public origin. Browser-originated application API requests go to same-origin /api/backend/*. The Next.js server calls FastAPI over NETPAY_BACKEND_INTERNAL_URL. Do not configure a browser-facing API base URL or expose upstream tokens to JavaScript.

## I1 — Operator registration

Record each step PASS / FAIL / N/A with date and redacted evidence only.

| # | Step | Evidence |
|---|---|---|
| 1 | Register a confidential server-side OIDC web client for NetPay | Client name and redacted settings |
| 2 | Enable Authorization Code + PKCE (S256) and client authentication supported by Zitadel | Redacted IdP configuration |
| 3 | Exact redirect URI is the frontend public origin plus /auth/callback/ | Redacted IdP app settings |
| 4 | Scopes include openid profile email; enable offline_access only if refresh tokens are intentionally required | Redacted scope configuration |
| 5 | Register the client_id as a trusted NetPay client in NetHubKe | Redacted admin confirmation |
| 6 | Configure frontend runtime secrets: OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_REDIRECT_URI, OIDC_SCOPES and OIDC_TRANSACTION_SECRET | Secret-manager key names only |
| 7 | Configure BFF_INTERNAL_SECRET identically in frontend and API secret stores | Secret-manager key names only |
| 8 | Configure a separate BFF_SESSION_ENCRYPTION_KEY in the API secret store | Key name only; never record value |
| 9 | Set NETPAY_BACKEND_INTERNAL_URL to the private FastAPI service origin | Redacted service configuration |
| 10 | Confirm public ingress does not expose /internal/* | Ingress configuration review |
| 11 | Confirm the API's NETHUB_API_BASE_URL and existing trusted-client integration | Redacted config evidence |
| 12 | Confirm the exact frontend origin and callback URI are used in the deployed configuration | Operator evidence |

The browser no longer performs OIDC token exchange. Do not register a public SPA client for the production NetPay frontend.

## Secret generation

Generate a dedicated Fernet encryption key:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Generate BFF_INTERNAL_SECRET and OIDC_TRANSACTION_SECRET as independent high-entropy random values using the organization's secret manager or cryptographically secure generator. The BFF internal secret must match across Next.js and FastAPI. Do not reuse M-Pesa encryption keys, database passwords or OIDC client secrets.

## I6 — Live staging acceptance

Run only after the owner has merged the implementation PR and Render/ingress has deployed both services. Record PASS/FAIL and timestamps.

| # | Check | Expected result |
|---|---|---|
| 1 | FastAPI /health/live | 200 |
| 2 | FastAPI /health/ready | 200; database=ok |
| 3 | Next.js /login/ | 200; branded sign-in page |
| 4 | Next.js /api/auth/status | 200; oidc_configured=true and bff_configured=true; no secret/token fields |
| 4a | Next.js /api/health/ready | 200; OIDC config, FastAPI readiness, BFF session table and encryption key are ready |
| 5 | Unauthenticated /dashboard/ | Redirects to /login/ |
| 6 | Complete browser sign-in | Zitadel → Next.js callback → dashboard |
| 7 | Session cookie inspection | HttpOnly, Secure in production, SameSite=Lax, Path=/; no upstream tokens in cookies |
| 8 | Browser storage inspection | No access/refresh token or PKCE verifier in localStorage/sessionStorage |
| 9 | Browser Network inspection | Human API calls use same-origin /api/backend/*; no direct browser calls to FastAPI /api/v1/* |
| 10 | Direct FastAPI /api/v1/auth/me without Bearer | 401/403 |
| 11 | BFF /api/backend/v1/auth/me without session | 401 |
| 12 | User without merchant membership | Profile may load; merchant data remains denied/empty |
| 13 | Admin grants one merchant membership | Only that merchant becomes visible |
| 14 | Attempt another merchant ID without membership | 403; no cross-merchant data |
| 15 | Logout | Server-side session revoked; cookie cleared; BFF requests return 401 |
| 16 | Access token expiry | Refresh occurs server-side if refresh token exists; otherwise session is invalidated and login is required |
| 17 | M2M client_credentials and payment APIs | Existing integration contract remains functional |
| 18 | Safaricom STK callback and optional C2B callbacks | Existing public callback URLs still reach FastAPI |
| 19 | /config.json on API | 404; former public SPA config endpoint removed |
| 20 | /internal/v1/bff/sessions without service secret | 401; route not reachable through public ingress |
| 21 | Realtime readiness | No idle WebSocket gateway/broker; documented ingress upgrade path reserved for a concrete future endpoint |

### Automated probe

Run from a machine that can reach both staging services:

    python backend/scripts/identity_staging_probe.py \
      --base-url https://<fastapi-api-origin> \
      --frontend-url https://<nextjs-frontend-origin>

The probe does not require or print tokens. It checks service health, unauthenticated API boundaries, public frontend readiness, login rendering, dashboard protection and BFF rejection without a session.

## Go / no-go

- I1 operator registration must be recorded as complete.
- I0–I6 acceptance remains open until the live evidence above and existing M2M/payment regression evidence are recorded.
- #239 acceptance additionally requires CI, both production images, secure OIDC/session behavior and deployed BFF verification.
- CI success is not live staging evidence.
- Do not promote to production or close #238 solely because the PR merged.

Record evidence in .trackers/task.md and .trackers/repo-state.md and comment on #233/#238 with redacted results. Never include token, secret or cookie values.
