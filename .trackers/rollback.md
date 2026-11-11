# Rollback — NetHubKe client program

**Last updated:** 2026-11-09

## Principles

## Issue #245 — independent Vercel frontend

- Revert the #245 PR to restore the previous frontend container deployment artifacts and routing if the Vercel deployment cannot be completed.
- The correction does not change payment schema, payment records, FastAPI business behavior or backend image identity.
- Vercel project configuration is external to this repository; restore the previous operator-managed frontend service only if the owner explicitly chooses that rollback path.
- Do not revert or rotate OIDC/BFF secrets as part of a code-only rollback unless a separate credential exposure or compromise is established.


- Prefer revert of merge commit on `dev` over history rewrite
- Never force-push protected branches
- Secrets: unset or rotate in secret manager; never commit values to roll back

## By milestone

| Slice | Rollback |
|-------|----------|
| I0 trackers only | Revert tracker commits; no runtime impact |
| I2 deploy README + readiness test | Revert PR; probes unchanged in behavior if only docs/tests |
| I3 SPA scopes/session | Revert FE/static; users re-login |
| I4 human APIs | Revert API routes; M2M unaffected if isolation held |
| I5 dashboard UI | Revert static export; public marketing pages independent if scoped |
| I1 ops (trusted client) | Revoke client in NetHubKe admin; IdP app disable |
| I6 staging | Scale or remove staging release; leave `main`/prod untouched |
| Membership rows | Soft-revoke via admin API; no payment ledger delete |

## Data

- PostgreSQL remains source of truth; do not drop financial tables to “undo” identity
- Membership revoke is sufficient to cut human dashboard access

## Production

- No production promote until I6 go + explicit approval
- If a bad image reached a cluster: roll image tag to previous known-good; run migrate only forward/compatible
