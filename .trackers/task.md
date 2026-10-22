# Task: Minimal NetPay rebuild — tracking baseline

**Last updated:** 2026-10-22  
**Branch:** `work/minimal-netpay-rebuild`  
**Base/integration branch:** `dev`  
**Application baseline commit:** `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`

## Goal

Track the approved minimal NetPay rebuild with evidence-based progress, acceptance criteria, and explicit separation between verified results and outstanding checks.

## Priority 0 — Agent handoff and continuity

**The repository must contain enough current information for a new agent or chat to resume safely without relying on hidden conversation history or asking the user to repeat established context.** Trackers, milestones, and linked issues are operational project state, not optional paperwork.

Before starting work, every agent must:
1. Read this file, `.trackers/repo-state.md`, `.trackers/milestone.md`, and `.trackers/rollback.md`.
2. Read `AGENTS.md`, `docs/REBUILD_SPEC.md`, and the applicable current shared skills from `https://github.com/NetHub-Ltd/skills-.git`.
3. Inspect the live branch refs and linked PR/issue state rather than trusting a potentially stale recorded SHA.
4. Identify the current milestone, last verified result, unresolved blockers/decisions, next safe action, and approval boundaries before changing application code.

During and after work, agents must update the relevant trackers and linked issue with meaningful decisions, exact evidence, changed state, blockers, and the next action. Re-fetch remote changes to confirm persistence. If the handoff state is missing, stale, or contradictory, reconcile it before proceeding with application changes. Never fill gaps with assumptions or use chat history as the only record of a decision.

A handoff is not complete merely because files exist: another agent must be able to determine **what is true, why, what remains, what is approved, and what to do next** from the repository and linked GitHub records.

## Scope and constraints

- Rebuild against `docs/REBUILD_SPEC.md`; do not restore pruned legacy application code.
- Work on `work/minimal-netpay-rebuild`; do not push directly to `dev` or `main`.
- Target future review PRs at `dev) once the working branch has commits not already on `dev`.
- Do not modify deployment manifests; Flux owns deployment reconciliation.
- Preserve frontend and backend `.env.example` files.
- Preserve CI, GHCR release/image publishing, and runtime contracts unless an approved change requires otherwise.
- Do not merge until all acceptance criteria are met.
- Keep this tracker current before work, during meaningful state changes, and after work.

## Current status

- [x] Tracker baseline created for the rebuild branch.
- [x] Record the known branch and PR/issue context.
- [x] Record known successful CI and frontend-build runs as historical reports, not fresh verification.
- [x] Make agent handoff/continuity a first-class operating requirement.
- [ ] Review full rebuild diff/commit range for unintended changes.
- [ ] Verify backend test/readiness checks from actual latest workflow results.
- [ ] Verify container smoke-test result from actual latest workflow results.
- [ ] Confirm frontend and backend `.env.example` files are present and fit current app configuration.
- [ ] Confirm release/GHCR workflow contract remains intact.
- [ ] Confirm acceptance criteria in `docs/REBUILD_SPEC.md` are satisfied.
- [ ] Perform browser-based visual/interaction review; not yet evidenced in this tracker.
- [ ] Verify that a fresh agent can resume from the trackers and linked GitHub records without relying on chat-only context.
- [ ] Reconcile this tracker with the latest run results before declaring the rebuild complete.

## Known GitHub references

- Working branch: https://github.com/NetHub-Ltd/NetPay/tree/work/minimal-netpay-rebuild
- Integration branch: https://github.com/NetHub-Ltd/NetPay/tree/dev
- Closed, unmerged PR #178 (closed because the head and base had identical commits at the time): https://github.com/NetHub-Ltd/NetPay/pull/178
- Tracking issue #179: https://github.com/NetHub-Ltd/NetPay/issues/179
- CI run #569 (previously reported successful; not freshly checked in this baseline): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757001572
- Frontend build run #15 (previously reported successful; not freshly checked in this baseline): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757002712

## Evidence rules

Use these labels in updates:
- **OBSERVED** — directly inspected in repository or GitHub.
- **VERIFIED** — confirmed by a test, workflow, command, or authoritative source.
- **INFERRED** — conclusion from observed evidence.
- **PROPOSED** — recommended but not yet approved/implemented.
- **UNKNOWN** — not established.

Do not mark a checkbox complete based only on intended implementation or a claim without supporting evidence. Always include exact run/commit/command references where available and distinguish "not run" from "failed" or "skipped".

## Changelog

- 2026-10-22: Created a fresh rebuild-specific tracker baseline after discovering the legacy `.trackers/` files on `main` were absent from the rebuild branch. Initial status is deliberately conservative; verification items remain open until checked against current evidence.
- 2026-10-22: Elevated agent handoff to Priority 0. Required reading order, freshness checks, evidence rules, and a resumability acceptance check are now explicit.