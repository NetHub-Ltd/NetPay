# NetPay milestones and handoff state

## Active milestone — Public theme and conversion polish (#222)

**Last updated:** 2026-11-14
**Verified base:** `dev` @ `f9674f9ad9693e9d496ab79901c667b13f9fec68`
**Branch:** `feat/frontend-theme-conversion`
**Status:** local implementation and validation complete; PR to `dev` pending.

| Criterion | Status |
|---|---|
| Centralize light/dark theme tokens and default to light | VERIFIED locally — shared semantic tokens and pre-paint preference restore |
| Provide accessible, persistent theme selection and responsive public navigation | VERIFIED locally — keyboard and persistence checks passed |
| Improve truthful public product messaging and conversion paths | VERIFIED locally — landing/product paths describe merchant-owned credentials, core STK and opt-in C2B without fabricated proof |
| Preserve SEO/indexing correctness and responsive layout | VERIFIED locally — nine routes, six viewport widths, both themes; metadata/sitemap check passed |
| Run frontend tests, lint, typecheck, dependency audits, build and server smoke | VERIFIED locally — 21 tests pass; both audits report zero vulnerabilities |
| Open a PR to `dev`; no merge/deployment | IN PROGRESS — branch is ready for commit/push and draft PR; owner retains merge authority |

Do not treat local accessibility/browser checks as user research or evidence of search-ranking or conversion uplift.

---

## Historical milestone — M-Pesa Core quality pass (#187)

**Last updated:** 2026-11-14
**Verified base:** `dev` @ `4246fbbce6361dea8d4c3506960a90aec2859ec9`
**Branch:** `feat/187-mpesa-core-quality`
**Status:** implementation/local validation complete; draft PR and external provider verification remain.

| Criterion | Status |
|---|---|
| Verify operation contracts against authoritative Daraja docs/sandbox; gate unresolved production capabilities | PARTIAL — catalogue checked; detail pages unavailable; existing provisional production gates retained |
| Enforce bounded response reads and bounded OAuth cache lifecycle | VERIFIED — 51 focused Core tests and 107 backend tests pass |
| Require validated operation-specific success responses; preserve ambiguity and retry safety | VERIFIED locally — operation registry, required STK correlation ID, rejection of empty/description-only acknowledgements, and failure classification tests |
| Simplify transport/operation ownership and improve typed contracts | VERIFIED locally — transport/OAuth extracted; finite operation enum and response registry |
| Add positive and negative unit coverage for all operations and security/failure boundaries | VERIFIED locally — 107 backend tests pass; no live provider contract tests were run |
| Run required backend, migration, container, frontend, and PR CI gates | LOCAL GATES VERIFIED — migration, backend, container build/smoke, frontend gates pass; GitHub PR checks pending |
| Open a PR to `dev`; no merge/deployment/live financial operation | IN PROGRESS — draft PR #265 open; GitHub Actions and Vercel checks pending |

Do not treat local test evidence as provider-contract verification or live acceptance.

---

## Historical milestones — NetHubKe client + deploy readiness

**Last updated:** 2026-11-11  
**Integration branch:** `dev`  
**Verified dev baseline for #239:** `5792662c22b7d4a5059f329d7b61427ca48769b5`  
**Status rule:** Do not mark VERIFIED without command/run/operator evidence. Use OBSERVED / VERIFIED / INFERRED / PROPOSED / UNKNOWN.

## Deploy contract (binding for all milestones)

| Item | Contract |
|------|----------|
| Frontend | Independent Vercel project; Root Directory `frontend`; normal Next.js server runtime |
| Images | FastAPI API only: `ghcr.io/nethub-ltd/netpay`; no frontend image |
| Release | FastAPI GHCR publish from **`main` only** |
| PRs | Always target **`dev`** |
| Runtime | FastAPI API + worker remain on their independent runtime; Vercel serves browser pages and the same-origin BFF |
| Readiness | FastAPI `/health/ready` = PostgreSQL (+ Redis report). **Not** NetHubKe/IdP |
| Secrets | Canonical names in `deploy/README.md` + `backend/.env.example`; Vercel server-only variables are documented in `deploy/README.md` |

## Program issues

| Milestone | Issue | Title |
|-----------|-------|-------|
| I0 | #232 | chore(trackers): NetHubKe-client program baseline |
| I1 | #233 | ops(identity): register NetPay public OIDC client + NetHubKe RS |
| I2 | #234 | chore(deploy): identity secret and rollout contract |
| I3 | #235 | fix(identity): SPA token lifecycle and honest scopes |
| I4 | #236 | feat(identity): membership-gated human read APIs |
| I5 | #237 | feat(ui): membership-aware dashboard surface |
| I6 | #238 | test(identity): staging E2E and deploy readiness gate |
| I7 | #239 | feat(platform): independent Next.js deployment, mandatory BFF and server-side identity |

## Milestone I0 — Tracker handoff baseline

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I0.1 | Program I0–I7 and issue links recorded | IN PROGRESS (this file) |
| I0.2 | Handoff read order and evidence rules explicit | IN PROGRESS |
| I0.3 | Deploy constraints table recorded | IN PROGRESS |
| I0.4 | Stale “dashboard placeholder only” language corrected | IN PROGRESS |
| I0.5 | PR to `dev` merges tracker baseline | OPEN |

## Milestone I1 — Platform registration (ops)

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I1.1 | IdP public OIDC client with Authorization Code + PKCE S256; no client secret; exact callback URI | OPEN — runbook in docs/ops/STAGING_IDENTITY.md |
| I1.2 | NetHubKe `trusted_clients` product=netpay | OPEN |
| I1.3 | No browser CORS dependency for BFF; verify server-to-server NetHubKe access | OPEN |
| I1.4 | Checklist in trackers without secrets | IN PROGRESS — template shipped |

## Milestone I2 — Deploy contract for identity

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I2.1 | `deploy/README.md` separates frontend OIDC and backend BFF secrets | IN PROGRESS |
| I2.2 | OIDC secrets frontend-only; BFF internal secret shared; encryption key API-only | IN PROGRESS |
| I2.3 | Rollout order + fail-closed human auth documented | IN PROGRESS |
| I2.4 | Readiness independent of NetHubKe VERIFIED by test | IN PROGRESS |
| I2.5 | No Flux apply by agent | VERIFIED policy |

## Milestone I3 — Token lifecycle

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I3.1 | Default scopes without unused `offline_access` (D1) | IN PROGRESS |
| I3.2 | 401 invalidates server-side session and clears opaque cookie | IN PROGRESS |
| I3.3 | Logout revokes server-side session and clears HttpOnly cookie | IN PROGRESS |
| I3.4 | Frontend lint/typecheck/build | OPEN |

## Milestone I4 — Membership-gated human APIs

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I4.1 | Human read route requires membership | IN PROGRESS |
| I4.2 | M2M scopes path unchanged | IN PROGRESS (no payment router edits) |
| I4.3 | Positive + negative tests | IN PROGRESS |
| I4.4 | Auth matrix in docs/identity-nethub-rs.md | IN PROGRESS |

## Milestone I5 — Dashboard surface

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I5.1 | Login/dashboard states (signed out / loading / no membership / membership / error) | IN PROGRESS |
| I5.2 | No payment data without ACL | IN PROGRESS |
| I5.3 | Frontend gates green | OPEN |

## Milestone I6 — Staging E2E + deploy readiness

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I6.1 | Staging checklist complete (VERIFIED steps) | IN PROGRESS — new two-origin BFF probe; live VERIFIED pending ops |
| I6.2 | M2M regression still OK | OPEN — manual I6 step 12 |
| I6.3 | Go/no-go recorded; no main merge without approval | OPEN |

## Milestone I7 — Mandatory independent Next.js + BFF (#239)

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I7.1 | Architecture and implementation contract approved by owner | VERIFIED — 2026-11-10 |
| I7.2 | Independent Next.js runtime, server-side OIDC, opaque sessions and mandatory HTTP BFF | IN PROGRESS on feat/239-nextjs-bff-runtime |
| I7.3 | FastAPI separation, separate images and ingress/deployment docs | IN PROGRESS |
| I7.4 | Login UI and dashboard session journey | IN PROGRESS |
| I7.5 | WSS ingress/security readiness documented; no idle gateway | IN PROGRESS |
| I7.6 | Security, payment regression, container and browser tests | IN PROGRESS |
| I7.7 | Post-merge live staging acceptance | NOT STARTED — owner deployment required |

## Historical notes

Earlier R0–R2 / public-site / mpesa_core tracker rows from Oct 2026 remain useful history but are **not** the active handoff surface for identity client work. Prefer this program table and linked issues #232–#239.


## Deployment correction — issue #245

- Status: PR #246 merged; the independent Vercel frontend deployment code is integrated.
- Next.js deployment is Vercel-managed; custom fonts are deferred and system font stacks are used for this pass.
- Frontend Dockerfile, frontend container smoke, frontend GHCR publishing and Kubernetes frontend Deployment/Service are removed by the #245 change set.
- FastAPI image, release, API, worker, M2M and Safaricom callback contracts remain unchanged.
- External acceptance after merge: Vercel project Root Directory/framework settings, server-only environment variables, and a private service-to-service path from Vercel to every required FastAPI BFF route, including the session-store endpoints.


## Public OIDC client correction — issue #248

- NetPay's Next.js server uses a **public OIDC client** with Authorization Code + PKCE (S256). Server-side callback handling does not require a client secret.
- Authorization-code and refresh-token grants send `client_id` in the form body; no HTTP Basic authentication or `client_secret` parameter is used.
- `OIDC_TRANSACTION_SECRET` remains a separate application secret protecting the short-lived encrypted PKCE transaction cookie.
- Operator registration contract is updated in issue #233. Live Zitadel/NetHubKe registration and staging sign-in remain unverified until operator evidence is recorded.
- Implementation: issue #248; [draft PR #249](https://github.com/NetHub-Ltd/NetPay/pull/249) from `fix/248-oidc-public-client` to `dev`. Vercel preview build is READY and GitGuardian passed; GitHub Actions are queued on head `60ae8398c0b453467dffe540ba718282b0b2d405`.
