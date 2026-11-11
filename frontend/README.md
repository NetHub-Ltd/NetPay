# NetPay frontend

NetPay's frontend is an independently deployed Next.js App Router application. It runs as a Node.js server and owns public pages, login/callback routes, the authenticated dashboard and the same-origin HTTP BFF.

## Local development

1. Configure backend/.env and frontend/.env.local from their example files.
2. Set the same random BFF_INTERNAL_SECRET in both services.
3. Configure a public OIDC client with Authorization Code + PKCE (S256). No Zitadel client secret is required. Its redirect URI must exactly match OIDC_REDIRECT_URI (local default: http://localhost:3000/auth/callback/).
4. Start FastAPI on port 8000 and Next.js on port 3000:

    cd backend
    uvicorn app.main:app --reload --port 8000

In another terminal:

    cd frontend
    npm ci
    npm run dev

## Server-only configuration

- NETPAY_BACKEND_INTERNAL_URL: private FastAPI origin used by Route Handlers and server components.
- BFF_INTERNAL_SECRET: shared service credential for private session-store endpoints; never prefix it with NEXT_PUBLIC_.
- OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_REDIRECT_URI and OIDC_SCOPES: public OIDC client configuration; token requests use client_id and PKCE, not a client secret.
- OIDC_TRANSACTION_SECRET: independent random secret (at least 32 characters) used to encrypt the short-lived PKCE transaction cookie.
- NEXT_PUBLIC_SITE_URL: public canonical origin for metadata and sitemap generation only.

The browser receives only a random HttpOnly session cookie. Access and refresh tokens are stored encrypted in the backend PostgreSQL session table. The frontend does not read tokens from browser storage or call FastAPI directly.

## Vercel deployment

Deploy this directory as an independent Next.js application. Set the Vercel project Root Directory to `frontend`, keep the Next.js framework preset and default install/build/output settings, and use the normal Next.js server runtime. Do not enable static export or add a frontend Docker image. Configure the server-only environment variables above in Vercel.

The Vercel server must be able to reach the configured `NETPAY_BACKEND_INTERNAL_URL`; do not assume a cluster-only hostname is reachable from Vercel.

## OIDC login diagnostics

Failed login initiation writes one structured JSON event to the Vercel function runtime log:

- Event: `oidc_login_initiation_failed`
- Fields: `request_id`, `category`, and `timestamp`
- Categories distinguish local configuration, discovery HTTP/response/issuer/endpoint failures, provider unreachability and unexpected internal failures.

The event intentionally excludes exception messages, stack traces, request URLs, cookies, authorization codes, tokens and environment-variable values. The browser receives only the existing generic configuration/provider error state; diagnostic details remain server-side.

To investigate a production failure:
1. Open the Vercel project `net-pay` and select the deployment serving the affected domain.
2. Open Logs / Runtime Logs and filter to the `/api/auth/login` function around the reproduction time.
3. Find the `oidc_login_initiation_failed` JSON event and use its category and request ID to correlate the failure.
4. Verify the configured issuer's `/.well-known/openid-configuration` response independently. Its `issuer` must exactly match `OIDC_ISSUER`; authorization, token and JWKS endpoints must be valid HTTPS URLs.
5. Do not paste secrets, tokens, authorization codes, cookies or raw provider responses into tickets or chat.

The login page's error banner is derived from its `error` query parameter. Reloading the same URL preserves the banner; visit `/login/` without the query string to clear the displayed state after investigation.

## API boundary

Browser requests use /api/backend/*. The BFF currently exposes an explicit GET allowlist for the dashboard's human profile, memberships, merchant summary and merchant payment list. Add new methods and routes deliberately with runtime validation, session checks, CSRF protection for mutations, safe cache headers and backend authorization preserved. Never turn the BFF into an arbitrary URL proxy.

FastAPI remains authoritative for merchant membership and payment authorization. Machine-to-machine payment clients and Safaricom callbacks retain their independent backend contracts.
