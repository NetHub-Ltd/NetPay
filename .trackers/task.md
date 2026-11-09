# Task tracker — NetHubKe client program

**Last updated:** 2026-11-09  
**Active implementation slice:** I3 (#235) token lifecycle on `feat/identity-i3-token-lifecycle`
**Integration branch:** `dev`  
**Do not** push directly to `dev` or `main`.

## Priority 0 — Agent handoff (mandatory)

Before changing application code, every agent must:

1. Read `.trackers/task.md` (this file), `repo-state.md`, `milestone.md`, `rollback.md`.
2. Read repo `AGENTS.md`, `docs/identity-nethub-rs.md`, `deploy/README.md`, and skills from https://github.com/NetHub-Ltd/skills-.git (CORE always; HUMAN-EXPERIENCE for UI; MARKET only if marketing).
3. Refresh live `dev` SHA, open issues #232–#239, open PRs — do not trust chat-only memory.
4. State: what is true, what is approved, blockers, next safe action.

Evidence vocabulary: **OBSERVED** | **VERIFIED** | **INFERRED** | **PROPOSED** | **UNKNOWN**.

## Product intent

NetPay is a multi-merchant M-Pesa Daraja gateway. **NetHubKe is the resource server** for human identity. NetPay:

- Does **not** verify human JWTs
- Forwards IdP Bearer to NetHubKe (`/api/v1/users/me`, sync on 404)
- Authorizes merchants via local `merchant_member` (identity ≠ automatic merchant access)
- Keeps **M2M** client-credentials for machine payment APIs

## Active task: I0 + I2

**Issues:** #232 (trackers), #234 (deploy contract)

**Must achieve**

- Program milestones and issues recorded for handoff
- `deploy/README.md` documents identity secrets and rollout; readiness independent of NetHubKe proven by test

**Non-goals this slice:** IdP registration (I1/#233), SPA scope/401 UX (I3/#235), membership APIs (I4/#236), dashboard UI (I5/#237), staging E2E (I6/#238), BFF (I7/#239)

**Decisions already approved (2026-11-09)**

- I3 default **D1**: drop unused `offline_access` until I7
- I4 minimal surface: membership-gated merchant read; M2M unchanged
- First code PR: I0+I2 only

**Next safe action after this PR merges**

1. Operator completes I1 (#233) or agent prepares staging checklist template
2. Implement I3 (#235) on new branch from latest `dev`

## Quality gates (when touching code)

| Stack | Gate |
|-------|------|
| Backend | pytest smoke_tests relevant modules; no secret logging |
| Frontend | `npm run lint`, `typecheck`, `build` when FE changes |
| Deploy docs | Canonical env names only; no real secrets in git |

## Approval boundaries

Never without explicit user confirmation: merge to `main`, GHCR release, Flux/cluster apply, production secret values in chat/git, closing issues as stale without safety rationale, scope expansion beyond open issues.
