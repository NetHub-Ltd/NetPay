# Task: Solidify NetPay core + align auth boundary with NetHub AS

**Status:** In progress (foundation PR)  
**Tier:** 2  
**Approved:** 2026-09-12 (user: approved / defaults OK)

## Goal

Solidify existing M-Pesa orchestration behavior and establish that **NetPay does not own end-user registration or login**. Users are authorized by **NetHub AS** and present a bearer token that NetPay will validate.

## Approved scope

1. Create `dev` from `main`; all future PRs target `dev`.
2. Initialize `.trackers/`.
3. Close #6 (cosmetic logging only).
4. Document NetHub AS as the sole user-auth authority; mark local password paths as transitional.
5. Add settings placeholders for AS issuer / JWKS / audience **without** switching validation yet.
6. Leave local `/auth/login`, admin bootstrap, and `X-Internal-Api-Key` working until a later approved cutover PR.

## Completed

- [x] Confirmed default branch `main`.
- [x] Created remote branch `dev` from `main` @ `709ceb9`.
- [x] Closed issue/PR #6 with rationale comment.
- [x] Initialized `.trackers/` (this file set).
- [x] Auth architecture note: `docs/auth-model.md`.
- [x] Config placeholders for NetHub AS in `backend/app/core/config.py`.

## Remaining (this PR)

- [ ] Open PR `chore/engineer-mode-foundation` → `dev`.
- [ ] User merges when satisfied.

## Explicitly out of scope

- Implementing JWKS / AS token validation (blocked on claim contract).
- Removing local `/auth/login` or password fields.
- User registration, invites, or profile management inside NetPay.
- Merging cosmetic logging changes.
- Large k3s hardening.
- New payment features.

## Active follow-ups (not authorized yet)

1. **NetHub AS integration** — validate JWT via JWKS; map claims → tenant/role; deprecate local login.
2. Decide fate of local `OAuthClient` table vs AS client credentials for M2M.
3. Expand pytest coverage for STK success/failure + webhook fan-out.
4. Harden `deploy/k8s/` (Ingress, secrets example, image name alignment).
5. Optional: re-open logging format chore if operators want aligned columns.

## Decisions made

- User auth/registration is **not** NetPay’s responsibility (NetHub AS).
- #6 closed as non-impacting.
- PRs always target `dev`.
- Local password auth remains until AS validation ships.

## Decisions still required (before AS cutover PR)

- Issuer URL / discovery, JWKS URL, algorithms, audience.
- Claim names for subject, tenant binding, role/scopes.
- How machine clients authenticate long-term (AS vs internal API key).

## Risks

- Config placeholders alone must not change runtime auth behavior (verified by design).
- Dashboard still depends on local login until cutover.

## Verification

- Existing acceptance tests must still pass.
- Frontend lint/build not required for this docs+config-only change; run if CI touches frontend paths.
- No secrets in commits.

## Debt introduced

- Local password login + admin env bootstrap remain as transitional paths (documented).
- AS placeholders present but unused until validation PR.

## Design decisions

- Auth boundary documented in `docs/auth-model.md` rather than only in chat.
- Internal envelope ingest keeps shared secret (`X-Internal-Api-Key`) separate from end-user AS tokens.
