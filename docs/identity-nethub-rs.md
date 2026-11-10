# NetPay human identity and NetHubKe resource-server contract

## Responsibility boundaries

| Component | Responsibility |
|---|---|
| Zitadel | User authentication and OIDC authorization-code flow |
| Next.js | Confidential OIDC client, callback handling, opaque application session and HTTP BFF |
| NetHubKe | Human identity resolution and product/resource access decisions |
| FastAPI | Merchant membership, tenant isolation and payment/business authorization |
| M2M auth | Existing client-credentials flow for machine integrations; independent of human sessions |

NetPay does not store passwords, authenticate users itself or locally verify human JWTs. FastAPI forwards the server-held IdP access token to NetHubKe for identity resolution. Merchant membership remains a separate local authorization check.

## Server-side OIDC flow

1. Browser navigates to the Next.js login route.
2. Next.js creates state, nonce and a PKCE verifier/challenge. The short-lived transaction cookie is encrypted, HttpOnly, SameSite=Lax and scoped to the callback path.
3. Browser is redirected to Zitadel's authorization endpoint using Authorization Code + PKCE.
4. Zitadel redirects to the exact registered Next.js callback URL.
5. Next.js validates state, exchanges the code server-side using the confidential client with client_secret_basic authentication, validates the RS256 ID-token signature and issuer/audience/expiry/nonce claims, then asks FastAPI to resolve the human identity through NetHubKe.
6. Next.js creates a random application session handle. Only its SHA-256 hash is stored in PostgreSQL. Access/refresh tokens are encrypted at rest using a dedicated BFF Fernet key.
7. Browser receives only an opaque HttpOnly, Secure-in-production, SameSite=Lax cookie. No upstream token is returned to JavaScript, browser storage or URLs.

The server-side session expires after eight hours. If an IdP refresh token is issued, the BFF rotates it server-side and uses optimistic versioning to handle concurrent requests. Without a refresh token, the session ends when the access token expires. Request offline_access only when the confidential client is configured to support refresh tokens.

## Mandatory browser HTTP BFF

All browser-originated application HTTP API calls use same-origin Next.js Route Handlers under /api/backend/*. The current explicit allowlist supports the dashboard's human profile, memberships, merchant summary and merchant payment list.

The BFF:
- Validates the opaque session and refreshes server-side credentials when available.
- Uses a configured private FastAPI origin; it never accepts a browser-selected upstream URL.
- Exposes only explicit route/method allowlists and validates path parameters/query values.
- Uses no-store responses and safe error translation.
- Never trusts client-supplied user, tenant, merchant or permission claims.
- Requires same-origin validation for state-changing browser operations such as logout.

Do not add a generic arbitrary URL proxy. New browser API methods must be added deliberately to the allowlist and covered by validation, CSRF and integration tests.

FastAPI continues to authorize every protected operation. It must not trust the fact that a request passed through the BFF as proof of merchant membership. The backend still rejects missing/invalid Bearer credentials and enforces merchant_member access.

## Private session persistence

FastAPI exposes internal service-to-service routes under /internal/v1/bff/sessions. They are excluded from OpenAPI and require the shared BFF_INTERNAL_SECRET. Public ingress must not route /internal/* to FastAPI. The Next.js service reaches them through NETPAY_BACKEND_INTERNAL_URL over the private service network.

The bffsession table stores:
- SHA-256 hash of the random browser session handle;
- encrypted access and optional refresh tokens;
- access-token expiry and absolute application-session expiry;
- optimistic token-rotation version and revocation timestamps.

BFF_SESSION_ENCRYPTION_KEY is a dedicated Fernet key and must not be reused for Daraja credential encryption. The shared BFF_INTERNAL_SECRET must be high entropy and identical in the frontend and API secret stores.

## Browser/API boundary

- Browser application code calls /api/backend/* only.
- Browser JavaScript cannot read IdP access/refresh tokens.
- The old public /config.json endpoint and browser sessionStorage token flow are removed.
- Next.js server-to-server calls use the private FastAPI service URL.
- FastAPI remains separately reachable for existing M2M clients and Safaricom callback URLs. Those contracts are not routed through a human browser session.
- Do not treat CORS as the security boundary. The browser has no upstream bearer token; the BFF holds it server-side and FastAPI still enforces its normal authorization rules.

## WSS readiness

Next.js Route Handlers are not a general-purpose WebSocket upgrade proxy. The current NetPay source has no live WebSocket endpoint requiring a gateway. Ingress must support HTTP/1.1 upgrades when a concrete realtime feature is added; reserve /ws/* for a dedicated authenticated realtime service. Authenticate the application session or a short-lived narrowly scoped connection credential, authorize each subscription against merchant membership, handle expiry/revocation and prevent cross-merchant event leakage. Do not introduce an idle gateway or broker.

## M2M and payment flows

The client-credentials token endpoint, merchant-scoped M2M permissions, STK Push, Safaricom callbacks, C2B registration and reconciliation remain independent of human OIDC sessions. The BFF must not change their authentication or callback contracts.

## Required frontend environment

- OIDC_ISSUER
- OIDC_CLIENT_ID
- OIDC_CLIENT_SECRET
- OIDC_REDIRECT_URI
- OIDC_SCOPES (openid profile email; offline_access only when intentionally enabled)
- OIDC_TRANSACTION_SECRET
- NETPAY_BACKEND_INTERNAL_URL
- BFF_INTERNAL_SECRET
- NEXT_PUBLIC_SITE_URL (public canonical URL only)

Backend requires NETHUB_API_BASE_URL, BFF_INTERNAL_SECRET and BFF_SESSION_ENCRYPTION_KEY in addition to its existing API/payment settings. See deploy/README.md and both .env.example files.
