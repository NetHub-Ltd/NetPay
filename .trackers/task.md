# Task: CI test/lint/build + auto-release to GHCR

**Status:** Implementation  
**Tier:** 2  
**Approved:** 2026-09-12 (proceed / defaults)

## Goal

Automated CI for tests/lint/build; on push to `main`, auto patch-tag, multi-arch GHCR push, GitHub Release with changelog. No manual tags.

## Approved scope

- Split `ci.yml` (PR/branch tests) and `release.yml` (main → version → GHCR → Release).
- PR targets: `main` and `dev`.
- Images only from main-driven tags.
- Patch bump; tag-only (no pyproject commit).
- `[skip release]` escape hatch.

## Completed

- [x] Rewrite `.github/workflows/ci.yml`
- [x] Add `.github/workflows/release.yml`
- [x] README CI section
- [x] Trackers for this task

## Remaining

- [x] PR → `dev` — https://github.com/NetHub-Ltd/NetPay/pull/8
- [ ] User merge; later promote `dev` → `main` to exercise release

## Out of scope

- AS auth cutover, app feature work, manual tag workflow as primary path.

## Verification

- PR CI green on this branch.
- After merge to main: tag + GHCR + Release (or `[skip release]` for dry merges).
