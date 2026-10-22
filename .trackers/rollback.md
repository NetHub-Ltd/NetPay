# NetPay rebuild rollback notes

**Last updated:** 2026-10-22

## Current change

This task adds tracking documentation only under `.trackers/` on `work/minimal-netpay-rebuild`. It does not intentionally change application code, database schema, runtime configuration, workflows, or deployment manifests.

## Recovery approach

- Before any future application change, record the exact pre-change working-branch commit in `.trackers/repo-state.md`.
- Prefer a reviewed revert commit for committed changes; do not reset or rewrite shared branch history without explicit approval.
- If a tracker-only update is wrong, correct it with a follow-up commit and preserve the history of the correction.
- Do not roll back or modify `main`, `dev`, Flux resources, or deployed resources as part of tracker repair.

## Known references

- Previous working baseline before tracker creation: `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`.
- `dev` was observed at the same SHA as the working branch at the last branch inspection.
- `main` was observed at `a55500c2838b8ad1cc637a121f2b30f7f88132d0` and must remain untouched by this task.

## Data and migrations

- No database migrations or data changes are part of tracker creation.

## Risks / unknowns

- This file is not a substitute for validating runtime rollback behavior of the rebuilt application.
- Exact rollback procedures for application images and release tags remain to be verified against the current release workflow and Flux configuration. Flux manifests are deliberately out of scope.
