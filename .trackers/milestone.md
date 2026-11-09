# NetPay milestones — NetHubKe client + deploy readiness

**Last updated:** 2026-11-09  
**Integration branch:** `dev`  
**Program tip at baseline write:** `82e85cb` (merge PR #231 — identity dashboard session)  
**Status rule:** Do not mark VERIFIED without command/run/operator evidence. Use OBSERVED / VERIFIED / INFERRED / PROPOSED / UNKNOWN.

## Deploy contract (binding for all milestones)

| Item | Contract |
|------|----------|
| Image | Next static export inside FastAPI image (`ghcr.io/nethub-ltd/netpay`) |
| Release | GHCR publish from **`main` only** |
| PRs | Always target **`dev`** |
| Runtime | k3s: migrate Job → API + worker; Flux/operators apply |
| Readiness | `/health/ready` = PostgreSQL (+ Redis report). **Not** NetHubKe/IdP |
| Secrets | Canonical names in `deploy/README.md` + `backend/.env.example` |

## Program issues

| Milestone | Issue | Title |
|-----------|-------|-------|
| I0 | #232 | chore(trackers): NetHubKe-client program baseline |
| I1 | #233 | ops(identity): register NetPay SPA on IdP + NetHubKe RS |
| I2 | #234 | chore(deploy): identity secret and rollout contract |
| I3 | #235 | fix(identity): SPA token lifecycle and honest scopes |
| I4 | #236 | feat(identity): membership-gated human read APIs |
| I5 | #237 | feat(ui): membership-aware dashboard surface |
| I6 | #238 | test(identity): staging E2E and deploy readiness gate |
| I7 | #239 | feat(identity): optional BFF session hardening |

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
| I1.1 | IdP public PKCE client + redirect URI | OPEN |
| I1.2 | NetHubKe `trusted_clients` product=netpay | OPEN |
| I1.3 | NetHubKe CORS allows NetPay origin | OPEN |
| I1.4 | Checklist in trackers without secrets | OPEN |

## Milestone I2 — Deploy contract for identity

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I2.1 | `deploy/README.md` lists NETHUB_* and OIDC_* secrets | IN PROGRESS |
| I2.2 | Canonical env names aligned with config/.env.example | IN PROGRESS |
| I2.3 | Rollout order + fail-closed human auth documented | IN PROGRESS |
| I2.4 | Readiness independent of NetHubKe VERIFIED by test | IN PROGRESS |
| I2.5 | No Flux apply by agent | VERIFIED policy |

## Milestone I3 — Token lifecycle

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I3.1 | Default scopes without unused `offline_access` (D1) | IN PROGRESS |
| I3.2 | 401 clears SPA session | IN PROGRESS |
| I3.3 | Logout clears token + PKCE keys | IN PROGRESS (clearSession on logout) |
| I3.4 | Frontend lint/typecheck/build | OPEN |

## Milestone I4 — Membership-gated human APIs

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I4.1 | Human read route requires membership | OPEN |
| I4.2 | M2M scopes path unchanged | OPEN |
| I4.3 | Positive + negative tests | OPEN |
| I4.4 | Auth matrix in docs/identity-nethub-rs.md | OPEN |

## Milestone I5 — Dashboard surface

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I5.1 | State matrix (out / loading / no membership / membership / error) | OPEN |
| I5.2 | No payment data without ACL | OPEN |
| I5.3 | Frontend gates green | OPEN |

## Milestone I6 — Staging E2E + deploy readiness

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I6.1 | Staging checklist complete (VERIFIED steps) | OPEN |
| I6.2 | M2M regression still OK | OPEN |
| I6.3 | Go/no-go recorded; no main merge without approval | OPEN |

## Milestone I7 — Optional BFF (after I6 + design approval)

| ID | Acceptance criterion | Status |
|----|----------------------|--------|
| I7.1 | Design approved | OPEN |
| I7.2 | httpOnly/BFF path + tests | OPEN |

## Historical notes

Earlier R0–R2 / public-site / mpesa_core tracker rows from Oct 2026 remain useful history but are **not** the active handoff surface for identity client work. Prefer this program table and linked issues #232–#239.
