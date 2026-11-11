# NetPay milestones — NetHubKe client + deploy readiness

**Last updated:** 2026-11-10  
**Integration branch:** `dev`  
**Verified dev baseline for #239:** `5792662c22b7d4a5059f329d7b61427ca48769b5`  
**Status rule:** Do not mark VERIFIED without command/run/operator evidence. Use OBSERVED / VERIFIED / INFERRED / PROPOSED / UNKNOWN.

## Deploy contract (binding for all milestones)

| Item | Contract |
|------|----------|
| Images | FastAPI API: `ghcr.io/nethub-ltd/netpay`; independent Next.js server: `ghcr.io/nethub-ltd/netpay-frontend` |
| Release | GHCR publish from **`main` only** |
| PRs | Always target **`dev`** |
| Runtime | k3s: migration Job → FastAPI API + worker + independent Next.js service; ingress routes app/API/callback traffic |
| Readiness | `/health/ready` = PostgreSQL (+ Redis report). **Not** NetHubKe/IdP |
| Secrets | Canonical names in `deploy/README.md` + `backend/.env.example` |

## Program issues

| Milestone | Issue | Title |
|-----------|-------|-------|
| I0 | #232 | chore(trackers): NetHubKe-client program baseline |
| I1 | #233 | ops(identity): register NetPay confidential OIDC web client + NetHubKe RS |
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
| I1.1 | IdP confidential server-side OIDC client + exact callback URI | OPEN — runbook in docs/ops/STAGING_IDENTITY.md |
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
