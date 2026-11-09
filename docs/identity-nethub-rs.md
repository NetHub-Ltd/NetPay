# Human identity via NetHubKe (resource server)

## Roles

| System | Role |
|--------|------|
| IdP (e.g. Zitadel) | Authorization Server — issues access tokens |
| NetHubKe | Resource Server — validates token, returns user JSON |
| NetPay | Forwards IdP Bearer to NetHubKe; does **not** verify human JWTs |

## Sequence (dashboard SPA + PKCE)

```text
Browser  → IdP authorize (PKCE)
Browser  ← authorization code
Browser  → IdP token endpoint (code + verifier) → access_token
Browser  → NetPay GET /api/v1/auth/me   Authorization: Bearer <access_token>
NetPay   → NetHubKe GET /users/me (same Bearer; 404 → sync → me)
NetPay   → Browser human profile JSON
Browser  → NetPay GET /api/v1/auth/memberships
```

**Auth mode:** `spa_pkce` (public client). No OIDC client secret in the static frontend or required for this flow.

## Config

### API (secret manager / env)

| Name | Purpose |
|------|---------|
| `NETHUB_API_BASE_URL` | NetHubKe API origin |
| `NETHUB_API_TIMEOUT_SECONDS` | Upstream timeout |
| `OIDC_ISSUER` | IdP issuer URL |
| `OIDC_CLIENT_ID` | **Public** SPA client id (must be in NetHubKe `trusted_clients`) |
| `OIDC_REDIRECT_URI` | e.g. `https://pay.example.com/auth/callback/` |
| `OIDC_SCOPES` | default `openid profile email offline_access` |

### Runtime discovery

`GET /config.json` (no auth) returns non-secret SPA settings: issuer, client id, redirect, scopes, flags.

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/config.json` | none |
| GET | `/api/v1/auth/me` | IdP Bearer |
| GET | `/api/v1/auth/memberships` | IdP Bearer |
| POST | `/api/v1/auth/memberships` | IdP Bearer + NetHubKe `is_admin` |
| DELETE | `/api/v1/auth/memberships/{merchant_id}` | IdP Bearer + admin |

## Auth matrix

| Token type | Handling |
|------------|----------|
| IdP access token (human) | `get_human_principal` → NetHubKe |
| NetPay M2M access token | `payments.security.require_scopes` |
| Daraja callbacks | Untrusted evidence |

## Merchant membership

Identity ≠ authorization. No auto-merchant on first login. Platform admin grants `merchant_member` rows.

## Staging checklist

1. Register NetPay SPA client id on NetHubKe `trusted_clients`.
2. Set `NETHUB_API_BASE_URL` and `OIDC_*` on NetPay.
3. IdP redirect URI matches `OIDC_REDIRECT_URI` (trailing slash if using `trailingSlash: true`).
4. Sign in at `/dashboard/` → callback → profile loads from `/api/v1/auth/me`.
5. Grant membership → `/api/v1/auth/memberships` non-empty.

## Deployment

Secret names and k3s rollout order for identity env vars are documented in [`deploy/README.md`](../deploy/README.md).

Program issues: #232–#239 (I0–I7). Staging registration is #233; deploy contract #234; token lifecycle #235.
