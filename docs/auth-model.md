# Auth model — NetPay

**Status:** Implemented direction (NetHub identity)  
**Authority:** NetPay does not own registration, login, or token validation.

## Principle

| Concern | System |
|---------|--------|
| User registration, login, MFA, session | **IdP (Zitadel)** via NetHub |
| Token validation + user profile | **NetHub API** (`GET /api/v1/users/me`) |
| Bearer handling in NetPay | **Forward token only** — never decode JWT, never store passwords/users as identity |
| Tenants / integrations / payments | **NetPay** (tenant `id` = NetHub `tenant_id`) |
| Platform admin | NetHub principal email listed in `ADMIN_EMAIL` / `ADMIN_EMAILS` |
| Worker / internal | `X-Internal-Api-Key` |

## Request path

```text
Client (IdP access token)
  → NetPay API Authorization: Bearer <token>
  → NetPay GET {NETHUB_API_BASE_URL}/api/v1/users/me  (same Bearer)
  → NetHub validates token and returns UserRead
  → NetPay uses Principal for tenant ACL (no local user row)
```

## Configuration

- `NETHUB_API_BASE_URL` — required for human auth (e.g. `https://api.nethub.co.ke`)
- `NETHUB_API_TIMEOUT_SECONDS` — default 8
- `ADMIN_EMAIL` / `ADMIN_EMAILS` — platform admin allowlist

## Removed

- `POST /auth/login` (password)
- Local HS256 access tokens for humans
- `POST /v1/tenants/assign-user` with password
- Admin bootstrap user with password

## Explicit non-goals for NetPay

- User self-registration
- Password storage
- JWT/JWKS validation inside NetPay

## SPA browser login (Zitadel / NetHub IdP)

NetPay dashboard is a **public SPA** (authorization code + PKCE). NetHubKe uses
Next.js Auth.js with server-side env (`OIDC_ISSUER`, `OIDC_CLIENT_ID`, optional
`OIDC_CLIENT_SECRET`). NetPay uses the **same variable names at image build**:

| Build arg (Docker / CI) | Becomes in SPA bundle | Notes |
|-------------------------|----------------------|--------|
| `OIDC_ISSUER` | `VITE_OIDC_ISSUER` | e.g. `https://auth.nethub.co.ke` |
| `OIDC_CLIENT_ID` | `VITE_OIDC_CLIENT_ID` | **SPA** app in Zitadel (PKCE) |
| `OIDC_REDIRECT_URI` | `VITE_OIDC_REDIRECT_URI` | e.g. `https://gateway.nethub.co.ke/auth/callback` |
| `OIDC_SCOPES` | `VITE_OIDC_SCOPES` | default `openid profile email offline_access` |

**Do not** bake `OIDC_CLIENT_SECRET` into the SPA. NetHubKe may use a secret on
the server; NetPay must not.

## Runtime SPA config (preferred)

NetPay serves **`GET /config.json`** (no auth) from process environment:

| Env | JSON field | Notes |
|-----|------------|--------|
| `OIDC_ISSUER` | `oidc_issuer` | e.g. `https://auth.nethub.co.ke` |
| `OIDC_CLIENT_ID` | `oidc_client_id` | Zitadel **SPA** (public) client |
| `OIDC_REDIRECT_URI` | `oidc_redirect_uri` | e.g. `https://pay.nethub.co.ke/auth/callback` |
| `OIDC_SCOPES` | `oidc_scopes` | default `openid profile email offline_access` |

The SPA prefers this runtime config and falls back to `VITE_OIDC_*` only for local Vite dev.
The same container image therefore works on GHCR, Render, and k3s — set env vars and restart.

CI (`release.yml`) reads GitHub Actions **variables**:
`vars.OIDC_ISSUER`, `vars.OIDC_CLIENT_ID`, `vars.NETPAY_OIDC_REDIRECT_URI`,
optional `vars.OIDC_SCOPES`.

Runtime FastAPI still needs `NETHUB_API_BASE_URL` (identity via NetHub API).
