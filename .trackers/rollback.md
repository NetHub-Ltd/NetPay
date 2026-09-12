# Rollback — CI/release automation

**Pre-change commit:** `709ceb9b05e7b0df939f77642e2176a8e83a9834`

## Rollback

1. Revert the merge commit on `dev` / `main`.
2. Or restore previous single `.github/workflows/ci.yml` from that commit.
3. Delete any unwanted `v*` tags created by the new pipeline: `git push origin :refs/tags/vX.Y.Z` and delete the GitHub Release.

## Notes

- Auto-created tags and GHCR images are the main external side effects.
- No database migrations in this change.
