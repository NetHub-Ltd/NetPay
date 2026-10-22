# Task: Minimal NetPay rebuild — tracking baseline

**Last updated:** 2026-10-22  
**Branch:** `work/minimal-netpay-rebuild`  
**Base/integration branch:** `dev`  
**Current known baseline commit:** `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`

## Goal

Track the approved minimal NetPay rebuild with evidence-based progress, acceptance criteria, and explicit separation between verified results and outstanding checks.

## Scope and constraints

- Rebuild against `docs/REBUILD_SPEC.md`; do not restore pruned legacy application code.
- Work on `work/minimal-netpay-rebuild`; do not push directly to `dev` or `main`.
- Target future review PRs at `dev` once the working branch has commits not already on `dev`.
- Do not modify deployment manifests; Flux owns deployment reconciliation.
- Preserve frontend and backend `.env.example` files.
- Preserve CI, GHCR release/image publishing, and runtime contracts unless an approved change requires otherwise.
- Do not merge until all acceptance criteria are met.
- Keep this tracker current before work, during meaningful state changes, and after work.

## Current status

- [x] Tracker baseline created for the rebuild branch.
- [x] Record the known branch and PR/issue context.
- [x] Record known successful CI and frontend-build runs.
- [ ] Review full rebuild diff/commit range for unintended changes.
- [ ] Verify backend test/readiness checks from actual latest workflow results.
- [ ] Verify container smoke-test result from actual latest workflow results.
- [ ] Confirm frontend and backend `.env.example` files are present and fit current app configuration.
- [ ] Confirm release/GHCR workflow contract remains intact.
- [ ] Confirm acceptance criteria in `docs/REBUILD_SPEC.md` are satisfied.
- [ ] Perform browser-based visual/interaction review; not yet evidenced in this tracker.
- [ ] Reconcile this tracker with the latest run results before declaring the rebuild complete.

## Known GitHub references

- Working branch: https://github.com/NetHub-Ltd/NetPay/tree/work/minimal-netpay-rebuild
- Integration branch: https://github.com/NetHub-Ltd/NetPay/tree/dev
- Closed, unmerged PR #178 (closed because the head and base had identical commits at the time): https://github.com/NetHub-Ltd/NetPay/pull/178
- Tracking issue #179: https://github.com/NetHub-Ltd/NetPay/issues/179
- CI run #569 (reported successful): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757001572
- Frontend build run #15 (reported successful): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757002712

## Evidence rules

Use these labels in updates:
- **OBSERVED** — directly inspected in repository or GitHub.
- **VERIFIED** — confirmed by a test, workflow, command, or authoritative source.
- **INFERRED** — conclusion from observed evidence.
- **PROPOSED** — recommended but not yet approved/implemented.
- **UNKNOWN** — not established.

Do not mark a checkbox complete based only on intended implementation or a claim without supporting evidence.

## Changelog

- 2026-10-22: Created a fresh rebuild-specific tracker baseline after discovering the legacy `.trackers/` files on `main` were absent from the rebuild branch. Initial status is deliberately conservative; verification items remain open until checked against current evidence.
