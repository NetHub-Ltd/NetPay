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
