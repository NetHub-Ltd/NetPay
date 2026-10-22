# NetPay rebuild rollback notes

**Last updated:** 2026-10-22

## Current change

This task updates handoff/process documentation only under `.trackers/` on `work/minimal-netpay-rebuild` and adds a dated continuity note to issue #179. It does not intentionally change application code, database schema, runtime configuration, workflows, or deployment manifests.

## Recovery approach

- Before any future application change, record the exact pre-change working-branch commit in `.trackers/repo-state.md`.
- Prefer a reviewed revert commit for committed changes; do not reset or rewrite shared branch history without explicit approval.
- If a tracker-only update is wrong, correct it with a follow-up commit and preserve the history of the correction.
- Do not roll back or modify `main`, `dev`, Flux resources, or deployed resources as part of tracker repair.

## Known references

- Previous working baseline before tracker creation: `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`.
- `dev` was observed at the same SHA as the working branch at the last branch inspection.
- `main` was observed at `a55500c2838b8ad1cc637a121f2b30f7f88132d0` and must remain untouched by this task.

## Handoff continuity

- The tracker handoff protocol is now documented in `.trackers/task.md` and `.trackers/repo-state.md`; milestone R0.5 records that documentation as verified.
- Independent resumability remains open under milestone R0.6. Do not treat the existence of instructions as proof that a fresh agent can resume correctly.
- Issue #179 contains a dated handoff note and canonical tracker links. Live branch refs remain authoritative over older branch-tip statements.

## Data and migrations

- No database migrations or data changes are part of tracker creation.

## Risks / unknowns

- This file is not a substitute for validating runtime rollback behavior of the rebuilt application.
- Exact rollback procedures for application images and release tags remain to be verified against the current release workflow and Flux configuration. Flux manifests are deliberately out of scope.


## Issue #180 rollback boundaries (2026-10-22)

- Issue: https://github.com/NetHub-Ltd/NetPay/issues/180
- Before implementation, record the current working branch tip and verify `dev` and `main` are unchanged.
- Settings and pool changes should be reverted through reviewed commits; do not reset or rewrite branch history.
- Moving `backend/migrations/` to `backend/alembic/` must preserve each migration file's contents and revision IDs. If Alembic cannot locate revisions after the move, revert the path/config reference changes together.
- No database reset, table drop, destructive migration, secret exposure, deployment manifest edit, or production database action is authorized.
- Render/Aiven runtime verification may require user-visible deployment logs/metadata. Do not change the database or claim the startup bug fixed solely from source inspection.
- If separate connection fields replace `DATABASE_URL`, document the required Render environment-variable update; do not silently assume Render has those variables configured. Keep the env example and code changes consistent.


## Implementation rollback/evidence update — 2026-10-22

- Implemented changes are on `work/minimal-netpay-rebuild`, latest observed tip `90951334628987c10cb77fb6f06f80bdedf9fe1f`; `dev` and `main` were rechecked and unchanged.
- CI #615 passed (15 passed, 1 warning), including Alembic migration and container smoke; backend readiness #169 and frontend lint/build #61 passed.
- Revert the settings/pool/Docker/test/workflow changes via reviewed commits if needed. Revert the Alembic directory/config/image-copy changes together so migrations remain discoverable as one unit.
- The compatibility bridge is temporary; removing it requires coordinated updates to external Render variables and deployment-owned secrets/manifests. Do not edit those manifests here.
- No database reset, schema drop, production DB action, Flux resource edit, branch reset, or history rewrite occurred.
- Actual Render/Aiven DB-off startup and Render schema remain unverified; do not treat CI's mocked failure test or CI PostgreSQL schema as production evidence.
