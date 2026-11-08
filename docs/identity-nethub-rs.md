# Human identity via NetHubKe (resource server)

**Status:** PR1 foundation on `dev` — client + `/api/v1/auth/me`. Dashboard session and merchant membership are separate issues.

## Roles

| System | Role |
|--------|------|
| IdP (e.g. Zitadel) | Authorization Server — issues access tokens |
| NetHubKe | Resource Server — validates token, returns user JSON |
| NetPay | Forwards IdP Bearer to NetHubKe; does **not** verify human JWTs |

## Sequence

```text
Client → NetPay  Authorization: Bearer <idp-access-token>
NetPay → NetHubKe GET /api/v1/users/me  (same Bearer)
  if 404 → POST /api/v1/users/sync then GET /me again
NetPay → Client  Human principal JSON
```

## Config (names only)

- `NETHUB_API_BASE_URL`
- `NETHUB_API_TIMEOUT_SECONDS` (default 8)

## Auth matrix

| Token type | NetPay handling |
|------------|-----------------|
| IdP access token (human) | `get_human_principal` → NetHubKe |
| NetPay M2M access token | `payments.security.require_scopes` |
| Daraja callbacks | Untrusted; signature/correlation — not identity |

## Endpoint

- `GET /api/v1/auth/me` — human only; returns `auth_type: human_nethub`
