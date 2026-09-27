# Auth model — NetPay

**Status:** Implemented (P2 #25 hard cut — 2026-09-27)  
**Authority:** Product decision — NetPay does not own end-user registration or login.

## Principle

| Concern | System |
|---------|--------|
| Authentication (who are you?) | **Keycloak** |
| Authorization + user context | **NetHub API** |
| Token validation + tenant enforcement | **NetPay** |
| Payment domain | **NetPay** |

## Request path

```text
User
  → authenticates with Keycloak
  → receives access token (aud = nethub-backend)
  → calls NetPay with Authorization: Bearer <token>
  → NetPay validates JWT (issuer, signature, exp, audience)
  → NetPay calls NetHub API GET /api/v1/users/me with the same token
  → NetHub returns user + tenant context
  → NetPay maps keycloak sub → local user binding and enforces can_access_tenant
```

## Audience

All access tokens **must** carry `aud=nethub-backend`. NetHub API rejects other audiences; NetPay enforces the same.

## Configuration

| Env | Purpose |
|-----|---------|
| `NETHUB_AS_ENABLED` | Default `true`. When JWKS+issuer set and not test, use Keycloak RS256. |
| `NETHUB_AS_ISSUER` | Keycloak realm issuer URL |
| `NETHUB_AS_JWKS_URL` | Keycloak JWKS URL |
| `NETHUB_AS_AUDIENCE` | Default `nethub-backend` |
| `NETHUB_API_BASE_URL` | NetHub API base (no trailing slash) for `/api/v1/users/me` |
| `ADMIN_KEYCLOAK_ID` | Bootstrap admin Keycloak sub (tests / first boot) |

## Removed (hard cut)

| Path | Fate |
|------|------|
| `POST /auth/login` | **410 Gone** — password login removed |
| End-user `hashed_password` | Nullable; no longer used for interactive auth |
| Frontend password form | Replaced with SSO / token entry |

## Kept

| Path | Purpose |
|------|---------|
| `GET /auth/me` | Current user from validated token |
| `POST /oauth/token` (client_credentials) | Local M2M — prefer Keycloak clients long-term |
| `X-Internal-Api-Key` on `/internal/*` | Edge → NetPay worker envelope (not end-user auth) |

## Test mode

When `ENVIRONMENT=test` (or JWKS unset), NetPay accepts HS256 tokens signed with `SECRET_KEY` so unit tests do not need a live Keycloak. Helpers mint these via `create_test_access_token`.

## Explicit non-goals

- User self-registration or password reset in NetPay
- NetHub-issued secondary session tokens for general SSO
- Hosting Keycloak login UI inside NetPay long-term (production should redirect to NetHub SSO)
