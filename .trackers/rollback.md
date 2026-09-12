# Rollback

**Last updated:** 2026-09-12

## Previous known-good

| Item | Value |
|------|--------|
| Commit | `709ceb9b05e7b0df939f77642e2176a8e83a9834` |
| Branch tip | `main` / `dev` at foundation start |
| Release/image | 1.1.0 / `ghcr.io/nethub-ltd/netpay` tags as of that commit |

## How to roll back this foundation work

1. If PR not merged: close/delete topic branch `chore/engineer-mode-foundation`.
2. If PR merged into `dev`: revert the merge commit on `dev`.
3. `dev` itself can remain (empty of product change) or be left as integration branch.
4. Closing #6 is irreversible without reopening the issue; product behavior unchanged either way.
5. Config placeholders are additive and inert; removing them is optional and non-urgent.

## Migrations / data

- None in this change set.

## Irreversible operations

- Issue/PR #6 closed (can be reopened on GitHub if needed).
