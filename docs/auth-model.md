# Auth model — NetPay

**Status:** Implemented (P2 #25 — NetHub-forwarded SSO, no JWKS)  
**Authority:** Product decision — NetPay does not own end-user registration or login.

## Principle

| Concern | System |
|---------|--------|
| Authentication (who are you?) | **Keycloak** |
| Authorization + user context | **NetHub API** |
| Payment domain + tenant isolation | **NetPay** |

NetPay **does not** call Keycloak JWKS and **does not** use JWT claims as business data.
It only forwards the client Bearer token to NetHub and uses the returned context.

## Request path

```text
User
  → authenticates with Keycloak
  → receives access token (aud = nethub-backend)
  → calls NetPay with Authorization: Bearer <token>
  → NetPay forwards the same token to NetHub GET /api/v1/users/me
  → NetHub validates the token and returns user + tenant context
  → NetPay applies can_access_tenant using that context
  → optional short TTL cache of NetHub context for latency
```

## Audience

Tokens accepted by NetHub must carry `aud=nethub-backend`. NetPay does not re-check audience; NetHub does.

## Configuration

| Env | Purpose |
|-----|---------|
| `NETHUB_API_BASE_URL` | **Required** in non-test environments. NetHub API base (no trailing slash). |
| `NETHUB_CONTEXT_CACHE_TTL_SEC` | Cache NetHub context (default 60). `0` disables. |
| `ADMIN_KEYCLOAK_ID` | Bootstrap admin sub for tests / first boot |

Legacy `NETHUB_AS_*` env vars are ignored at runtime (kept so old env files do not crash).

## Removed

| Path | Fate |
|------|------|
| `POST /auth/login` | **410 Gone** |
| Keycloak JWKS validation in NetPay | Removed — NetHub is the resource server for identity |
| End-user passwords in NetPay | Not used |

## Kept

| Path | Purpose |
|------|---------|
| `GET /auth/me` | Current user derived from NetHub context |
| `POST /oauth/token` (client_credentials) | Local M2M — prefer Keycloak clients long-term |
| `X-Internal-Api-Key` on `/internal/*` | Edge → NetPay worker envelope |

## Test mode

When `ENVIRONMENT=test` and `NETHUB_API_BASE_URL` is empty, NetPay accepts HS256 test tokens signed with `SECRET_KEY` so unit tests run without live NetHub. This path is disabled outside test.

## Explicit non-goals

- User self-registration or password reset in NetPay
- NetHub-issued secondary session tokens for general SSO
- NetPay depending on Keycloak availability or claim schemas
