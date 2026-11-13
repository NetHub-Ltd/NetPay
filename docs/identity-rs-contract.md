# NetPay human identity contract

## Roles

| System | Role |
|--------|------|
| **IdP** (Zitadel / NetHub auth) | Authenticates the human; issues access tokens |
| **NetHubKe** | **Resource server (RS)** for identity — `GET /api/v1/users/me`, `POST /api/v1/users/sync` |
| **NetPay frontend** | Public OIDC client (Auth.js); holds IdP tokens server-side only |
| **NetPay backend** | Separate product API (merchants, payments). Resolves humans **only** via NetHubKe |

## Flow

1. Browser signs in via Auth.js → IdP → callback `/api/auth/callback/oidc`.
2. Access token stays in the Auth.js JWT (HttpOnly cookie). Browser JS does not read it.
3. Dashboard calls same-origin `/api/backend/*`; the BFF attaches `Authorization: Bearer <IdP access token>` to NetPay FastAPI.
4. NetPay `get_human_principal` dependency calls `resolve_human(token)`:
   - Optional Redis cache (token SHA-256 key, short TTL)
   - Else NetHubKe `/me`, on 404 `/sync` then `/me`
5. Returned **HumanPrincipal** is the NetHubKe user (id, email, flags). Merchant membership is NetPay-local and checked separately.

## Caching

- Purpose: reduce RS latency only — not a durable identity store.
- Key: `netpay:rsuser:v1:{sha256(access_token)}`
- TTL: `NETHUB_USER_CACHE_TTL_SECONDS` (default 45; `0` disables)
- Never cache 401/403 or invalid payloads
- Redis down → live RS calls (degrade open on cache path)

## Non-goals

- NetPay does not verify IdP JWTs locally for human routes (forwards Bearer to RS).
- Auth.js session claims are not the product user profile.
- M2M / M-Pesa clients use separate auth; do not use `get_human_principal`.
