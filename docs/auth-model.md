# Auth model — NetPay

**Status:** Target architecture (2026-09-12)  
**Authority:** Product decision — NetPay does not own end-user registration or login.

## Principle

| Concern | System |
|---------|--------|
| User registration, login, password, MFA, session UX | **NetHub AS** (Authorization Server) |
| Token issuance for humans and (preferably) machines | **NetHub AS** |
| Bearer token validation and claim → tenant/role mapping | **NetPay** |
| Tenants, integrations, payment intents, webhooks, events | **NetPay** |
| Daraja credentials and STK/C2B orchestration | **NetPay** |

Clients obtain a token from NetHub AS and call NetPay APIs with `Authorization: Bearer <token>`. NetPay must not become a second identity provider.

## Target request path

```text
User / service
    → authenticates with NetHub AS
    → receives access token
    → calls NetPay with Bearer token
    → NetPay validates token (issuer, signature, audience, expiry)
    → NetPay reads claims (subject, tenant binding, role/scopes)
    → enforces can_access_tenant / admin rules
```

## Expected claims (to be confirmed with AS owners)

Exact names are **not finalized**. The following are the semantic requirements:

- **Subject** — stable user or client identifier.
- **Tenant binding** — which NetPay tenant the caller may access (unless platform admin).
- **Role or scopes** — at least distinguish platform admin vs tenant-scoped operator.
- **Audience** — value NetPay will enforce so tokens for other services are rejected.
- **Expiry** — standard `exp`.

Until the AS contract is agreed, validation code must not switch production traffic.

## Transitional (legacy) paths still present in code

These remain for local development and until the AS validation PR is approved and shipped:

| Path | Purpose | Target fate |
|------|---------|-------------|
| `POST /auth/login` | Local email/password → NetPay-issued JWT | Remove or disable in production after AS cutover |
| Admin bootstrap from `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Seed first admin in empty DB | Keep as break-glass/bootstrap only, or replace with AS-provisioned admin mapping |
| `POST /v1/tenants/assign-user` (password) | Create/bind local user with password | Replace with AS identity binding (no password stored in NetPay) |
| `POST /oauth/token` + `oauth_clients` table | Local client_credentials M2M | Prefer NetHub AS clients; decide keep/remove in follow-up |
| `X-Internal-Api-Key` on `/internal/events` | Worker envelope ingest | **Keep** as service-to-service secret (not end-user auth) |

## Configuration placeholders

See `backend/app/core/config.py`:

- `NETHUB_AS_ISSUER`
- `NETHUB_AS_JWKS_URL`
- `NETHUB_AS_AUDIENCE`
- `NETHUB_AS_ENABLED` (default `false` — local JWT validation remains active)

When `NETHUB_AS_ENABLED=true` and validation is implemented, NetPay will prefer AS tokens. Until then, placeholders are inert.

## Explicit non-goals for NetPay

- User self-registration or invite flows.
- Password reset or credential storage for humans (beyond transitional local users).
- Hosted login UI as the long-term entry point (dashboard should ultimately use NetHub AS).

## Related code (current)

- `backend/app/core/security.py` — HS256 JWT create/decode with `SECRET_KEY`.
- `backend/app/api/deps.py` — `get_current_user`, `require_admin`, `can_access_tenant`.
- `backend/app/api/routes/auth.py` — login, me, local OAuth token, create OAuth client.
- `backend/app/services/bootstrap.py` — admin ensure on startup.
