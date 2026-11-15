# Repository state — NetPay

## Active implementation — issue #222

**Current active issue:** #222 — centralize light/dark themes and polish public conversion
**Current implementation branch:** `feat/frontend-theme-conversion`
**Verified implementation base:** `dev` @ `f9674f9ad9693e9d496ab79901c667b13f9fec68`
**Current implementation state:** implementation and local validation complete; PR creation pending.
**PR target:** `dev`; repository owner retains merge authority.

The public-site redesign centralizes semantic light/dark tokens, defaults to light, and adds accessible theme preference persistence. Public pages now present a factual M-Pesa Daraja product story and clearer API/access paths. No backend/payment contracts, analytics, production secrets, or deployment behavior changed.

**Local evidence:** frontend clean install completed; 21 tests, lint, strict typecheck, both dependency audits, production build and host-process smoke passed. Browser QA covered 9 routes at six viewport widths in both themes with zero axe violations; rendered metadata and sitemap checks passed. GitHub CI is pending PR creation.

---

## Historical implementation — issue #187

**Current active issue:** #187 — complete M-Pesa Core quality pass
**Current implementation branch:** `feat/187-mpesa-core-quality`
**Verified implementation base:** `dev` @ `4246fbbce6361dea8d4c3506960a90aec2859ec9`
**Current implementation state:** code and local validation complete; draft PR #265 is open, with GitHub checks pending. Detailed provider-contract verification remains limited by inaccessible official operation pages.
**PR target:** `dev`; repository owner retains merge authority.

The change adds bounded response streaming, a bounded OAuth token cache and fixed lock stripes, a typed operation/response registry, and stricter acknowledgement validation without moving application authorization or idempotency into Core. Existing production gates for provisional products remain unchanged. The official catalogue was checked, but detailed operation contracts could not be independently verified. No migrations, deployment changes, live credentials, production transactions, or merges are in scope.

**Local evidence:** Alembic upgrade succeeded; backend suite 107 passed; FastAPI image build and container smoke passed; frontend lint, strict typecheck, security tests (17 passed), production build, and host-process smoke passed. GitHub Actions and Vercel checks on PR #265 remain pending.

---

## Historical identity/deployment handoff

**Current active issue:** #248 — public OIDC client + PKCE  
**Current implementation branch:** `fix/248-oidc-public-client`  
**Verified implementation base:** `dev` @ `4ea426f20af6d273e1bd82c5ca2fefdb2f7fa0c5`  
**Current implementation state:** draft PR #249 open; Vercel preview READY and GitGuardian passed; GitHub Actions queued on head `60ae8398c0b453467dffe540ba718282b0b2d405`. The owner retains final merge authority.

## Current deployment contract

| Component | Current target |
|---|---|
| Next.js | Independent Vercel project; Root Directory `frontend`; normal Next.js server runtime |
| FastAPI | Independent API runtime; existing GHCR image/release lifecycle retained |
| Browser API | Same-origin Next.js BFF only; no direct browser-to-FastAPI calls |
| OIDC/session | Server-side OIDC; opaque HttpOnly session; upstream tokens encrypted in PostgreSQL |
| Backend ingress | Existing M2M API and Safaricom callback paths only; no frontend service or public internal session routes |
| Fonts | System sans-serif/monospace stacks for this deployment pass; branded fonts deferred |

Vercel server functions must be able to reach the configured `NETPAY_BACKEND_INTERNAL_URL`. A private Kubernetes-only hostname is not assumed reachable from Vercel. Live network reachability remains an operator/staging acceptance item.

## #245 implementation evidence

- `dev` was recreated from `main` at `b24acde75ea9a6b8161ea772247410c8d28b45d4`.
- Topic branch `chore/245-vercel-frontend-deployment` is based on that commit.
- Next.js config uses the normal server runtime; Google-hosted font imports are removed in favor of the CSS system font stacks.
- Local Compose no longer builds or starts a frontend container.
- Frontend CI uses a host-process Next.js production smoke test; backend container CI is retained.
- Frontend GHCR publishing and Kubernetes frontend routing have been removed; FastAPI image/release behavior remains unchanged.
- PR #246 records Vercel provider checks and GitHub Actions results for its current head. No live Vercel-to-FastAPI private network test or production deployment has been performed.
## Branch and delivery model

| Ref | Role |
|---|---|
| main | Release source; FastAPI GHCR release remains main-only |
| dev | Integration branch; PR target |
| chore/245-vercel-frontend-deployment | Current #245 implementation branch |

The owner performs the final merge. No direct push to dev/main, no rebase/squash/reset/force-push and no production deployment by the agent.

## Historical #239 identity work

The previous #239 implementation and I0–I6 work remain historical context. Do not interpret their old standalone/container deployment wording as the current target; issue #245 supersedes that deployment detail. Existing live identity acceptance remains separate and must not be marked complete from CI alone.

**Last updated:** 2026-11-10  
**Verified integration baseline:** dev @ 5792662c22b7d4a5059f329d7b61427ca48769b5  
**Implementation branch:** feat/239-nextjs-bff-runtime  
**Implementation state:** in progress; awaiting CI and PR review.

## Branch and delivery model

| Ref | Role |
|---|---|
| main | Release source; GHCR release workflow remains main-only |
| dev | Integration branch; PR target |
| feat/239-nextjs-bff-runtime | Approved #239 implementation branch from verified dev baseline |

The owner performs the final merge. No direct push to dev/main, no rebase/squash/reset/force-push and no production deployment by the agent.

## Current architecture target

| Component | Target |
|---|---|
| Next.js | Independent Node.js server, standalone output, public site/login/dashboard and HTTP BFF |
| FastAPI | Independent API service; payment/domain logic, M2M, merchant authorization, callbacks and BFF session persistence |
| OIDC | Confidential server-side Authorization Code + PKCE |
| Browser session | Opaque HttpOnly cookie; no IdP tokens in JavaScript/storage |
| Session persistence | PostgreSQL hash of session handle; Fernet-encrypted access/refresh tokens |
| Browser API | Same-origin Next.js BFF only |
| M2M / Safaricom | Existing API and callback contracts retained |
| WSS | Ingress readiness documented; no gateway until a concrete realtime use case |

## I0–I6 identity work

PRs #240–#243 delivered the majority of I0–I6 code and CI work. The following remain separate operator/live acceptance items:
- I1: actual confidential IdP registration and NetHubKe trusted-client configuration/evidence.
- I6 / issue #238: live staging browser and API evidence; CI alone is insufficient.
- Existing M2M/payment regression evidence must be recorded as part of staging acceptance.

Do not mark I0–I6 live acceptance complete from this #239 PR. Keep #238 open until evidence is recorded.

## #239 implementation

- Issue #239 was re-scoped and approved on 2026-11-10 as mandatory independent Next.js + BFF + server-side identity.
- Branch feat/239-nextjs-bff-runtime created from dev SHA 5792662c22b7d4a5059f329d7b61427ca48769b5.
- Changes are in progress. Initial CI on an earlier PR head passed frontend lint/typecheck/build and backend readiness, but found two test-fixture/assertion issues plus a frontend container-smoke failure. The test issues are corrected; local Node security-helper tests pass 7/7. A fresh full CI run on the current head remains outstanding.
- PR #244 is open against dev. No live staging deployment has been performed.
- Render staging currently needs an independently deployed frontend service and operator-managed OIDC/runtime configuration after merge.

## CI and deployment

Preserve the FastAPI image identity ghcr.io/nethub-ltd/netpay and release behavior; add ghcr.io/nethub-ltd/netpay-frontend. CI must build/test both independently. Kubernetes and Compose now target separate services in this branch. Render configuration is documented as a two-service operator rollout; no live settings are assumed.

## Evidence rules

Use OBSERVED / VERIFIED / INFERRED / PROPOSED / UNKNOWN. CI results verify CI only. Live staging, operator configuration and deployment status require direct evidence. Never record secrets, access tokens, refresh tokens or session cookies.


## Public OIDC client correction — issue #248

- Current contract: Next.js performs the OIDC callback and token exchange server-side as a public OIDC client using Authorization Code + PKCE (S256). No Zitadel client secret is configured or sent.
- Token endpoint requests carry `client_id` in the form body for both authorization-code and refresh-token grants. No HTTP Basic authentication is used.
- `OIDC_TRANSACTION_SECRET` remains required only to encrypt the short-lived PKCE transaction cookie; it is an application secret, not an IdP client secret.
- Operator registration issue #233 has been corrected to the public-client contract. Live IdP registration and end-to-end staging login remain unverified.
- Implementation issue #248; [draft PR #249](https://github.com/NetHub-Ltd/NetPay/pull/249) from `fix/248-oidc-public-client` to `dev`; Vercel preview READY, GitGuardian success, GitHub Actions queued.
