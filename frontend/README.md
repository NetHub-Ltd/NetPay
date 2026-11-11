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
- The browser still receives only a generic `error` query value (`configuration` or `provider`). Technical detail stays server-side.

### Allowlisted `category` values

| category | Meaning | Typical fix |
|---|---|---|
| `missing_env` | A required `OIDC_*` server env var is unset or empty | Set `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_REDIRECT_URI`, `OIDC_TRANSACTION_SECRET` on the Vercel project that serves the live host |
| `redirect_origin_mismatch` | `OIDC_REDIRECT_URI` origin ≠ request origin | Set `OIDC_REDIRECT_URI` to `https://<live-frontend-host>/auth/callback/` (trailing slash). Live host is currently `netpay.nethub.co.ke` |
| `transaction_secret_invalid` | `OIDC_TRANSACTION_SECRET` shorter than 32 characters | Generate a new ≥32-char random secret |
| `issuer_invalid` | Issuer URL invalid or not HTTPS in production | Fix `OIDC_ISSUER` |
| `redirect_uri_invalid` | Redirect URI invalid or not HTTPS in production | Fix `OIDC_REDIRECT_URI` |
| `scopes_invalid` | `OIDC_SCOPES` does not include `openid` | Use `openid profile email` |
| `discovery_*` / `internal` | IdP discovery or unexpected failure | Check IdP availability and issuer metadata |

The event intentionally excludes exception messages, stack traces, request URLs, cookies, authorization codes, tokens and environment-variable values.

### Safe status endpoint

`GET /api/auth/status` returns:

```json
{
  "oidc_configured": true,
  "bff_configured": true,
  "checks": {
    "issuer_present": true,
    "issuer_https": true,
    "client_id_present": true,
    "redirect_uri_present": true,
    "redirect_uri_https": true,
    "redirect_origin_matches_site": true,
    "transaction_secret_ok": true,
    "scopes_ok": true
  }
}
```

All `checks` values are booleans. No secret values or full redirect URLs are returned. `redirect_origin_matches_site` compares `OIDC_REDIRECT_URI` origin to `NEXT_PUBLIC_SITE_URL` origin — set both to the **same** public frontend origin (for production: `https://netpay.nethub.co.ke`).

### Investigate a production failure

1. Open the Vercel project that serves `netpay.nethub.co.ke` and select the active deployment.
2. Runtime Logs → filter `/api/auth/login` around the reproduction time.
3. Find `oidc_login_initiation_failed` and read `category` + `request_id`.
4. Optionally `curl -s https://netpay.nethub.co.ke/api/auth/status` and inspect `checks` (booleans only).
5. Confirm Zitadel redirect URI equals `OIDC_REDIRECT_URI` exactly (including trailing slash).
6. Do not paste secrets, tokens, authorization codes, cookies or raw provider responses into tickets or chat.

The login page error banner comes from the `error` query parameter. Visit `/login/` without the query string to clear it after fixing configuration.

## API boundary

Browser requests use /api/backend/*. The BFF currently exposes an explicit GET allowlist for the dashboard's human profile, memberships, merchant summary and merchant payment list. Add new methods and routes deliberately with runtime validation, session checks, CSRF protection for mutations, safe cache headers and backend authorization preserved. Never turn the BFF into an arbitrary URL proxy.

FastAPI remains authoritative for merchant membership and payment authorization. Machine-to-machine payment clients and Safaricom callbacks retain their independent backend contracts.
