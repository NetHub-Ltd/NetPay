# Staging identity — NetPay as NetHubKe client

**Issues:** #233 (I1 platform registration), #238 (I6 staging E2E gate)  
**Secrets:** never paste production tokens, client secrets, or admin emails into git or public issues.

## Roles

| System | Action |
|--------|--------|
| IdP | Public OIDC app, PKCE, redirect URI |
| NetHubKe RS | `trusted_clients` row + CORS |
| NetPay | `NETHUB_*` + `OIDC_*` secrets; same-origin SPA |

## I1 — Platform registration checklist

Record each step as **PASS / FAIL / N/A** with date (no secret values).

| # | Step | Evidence type |
|---|------|----------------|
| 1 | Create IdP **public** client (PKCE, no client secret in SPA) | Operator note (client name only) |
| 2 | Redirect URI exact match: `{PUBLIC_ORIGIN}/auth/callback/` (trailing slash per Next) | Screenshot of IdP app settings redacted |
| 3 | Scopes: `openid profile email` (no `offline_access` until I7) | Operator note |
| 4 | NetHubKe admin: register `client_id` in `trusted_clients` with `product=netpay`, active | Admin API or console (id redacted) |
| 5 | NetHubKe `ALLOWED_ORIGINS` includes NetPay public origin | Config change ticket |
| 6 | Bootstrap platform admin email(s) in NetHubKe secret store for membership grants | Secret manager path only |
| 7 | Negative: unknown client_id → NetHubKe 401 | Command result without token |

### NetHubKe trusted client (shape only)

```http
POST /api/v1/admin/trusted-clients
Authorization: Bearer <admin-idp-token>
Content-Type: application/json

{
  "client_id": "<netpay-spa-public-client-id>",
  "name": "NetPay SPA",
  "product": "netpay",
  "notes": "PKCE public client for pay staging"
}
```

## NetPay secret fill (staging)

Canonical keys — see `deploy/README.md` and `backend/.env.example`:

- `NETHUB_API_BASE_URL`
- `NETHUB_API_TIMEOUT_SECONDS`
- `OIDC_ISSUER`
- `OIDC_CLIENT_ID`
- `OIDC_REDIRECT_URI`
- `OIDC_SCOPES=openid profile email`

Rollout: secrets → migrate Job if needed → API/worker. Identity missing ⇒ human auth fail-closed; M2M + public static + probes still work.

## I6 — Staging E2E checklist

Run against **staging origin** only. Mark VERIFIED with timestamp.

| # | Check | How |
|---|--------|-----|
| 1 | `GET /health/live` → 200 | curl |
| 2 | `GET /health/ready` → 200, `database=ok` | curl |
| 3 | `GET /config.json` → `oidc_configured: true`, **no** secret fields | curl + review JSON |
| 4 | Browser: `/dashboard/` → Sign in → IdP → `/auth/callback/` → profile | Manual |
| 5 | `GET /api/v1/auth/me` with Bearer → 200 profile | curl or Network tab |
| 6 | Memberships empty before grant | UI + API |
| 7 | Platform admin grants membership | Admin API |
| 8 | Memberships non-empty; select merchant | UI |
| 9 | `GET /api/v1/auth/merchants/{id}` → 200 | curl |
| 10 | `GET /api/v1/auth/merchants/{id}/payments` → 200 (list may be empty) | curl |
| 11 | Without membership → 403 `merchant_membership_required` | curl other merchant id |
| 12 | M2M client_credentials still issues token / payment path OK | existing M2M smoke |
| 13 | 401 clears SPA session (sign-in again) | Manual after token revoke/expiry |

### Automated probe (no secrets in output)

From a machine that can reach staging:

```bash
# Unauthenticated contract probes (safe in CI against a URL)
python backend/scripts/identity_staging_probe.py --base-url https://pay-staging.example.com

# Optional: human path when ACCESS_TOKEN is in env (never log the token)
NETPAY_PROBE_ACCESS_TOKEN=... python backend/scripts/identity_staging_probe.py \
  --base-url https://pay-staging.example.com --with-auth
```

Exit code 0 = all selected checks passed.

## Go / no-go

| Decision | Criteria |
|----------|----------|
| **Go for broader staging use** | I1 rows 1–7 PASS; I6 rows 1–13 PASS; residual risks listed |
| **No production / main release** | Still requires explicit approval; I7 BFF optional for high-value merchants |
| Residual risks | Access token in `sessionStorage` (XSS) until #239 |

## Recording results

Update `.trackers/task.md` and `.trackers/repo-state.md` with PASS/FAIL tables (no secrets). Comment on issues #233 and #238 with a redacted summary.
