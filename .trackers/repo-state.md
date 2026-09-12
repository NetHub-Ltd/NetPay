# Repository State

**Last updated:** 2026-09-12

| Field | Value |
|-------|--------|
| Repository | https://github.com/NetHub-Ltd/NetPay.git |
| Default branch | `main` (protected) |
| Integration branch | `dev` (all PRs target `dev`) |
| Current topic branch | `chore/engineer-mode-foundation` |
| Known-good commit (main/dev tip at foundation) | `709ceb9b05e7b0df939f77642e2176a8e83a9834` |
| App version | 1.1.0 |
| Preferred deployment | k3s (`deploy/k8s/`) |
| Container images | `ghcr.io/nethub-ltd/netpay` |

## Implementation state

- Multi-tenant M-Pesa gateway (FastAPI + React SPA) is functional for STK Push, C2B URL registration, signed webhooks, internal envelope ingest.
- Engineer Mode trackers initialized.
- Issue/PR #6 (logging v1.3.2 cosmetic) closed 2026-09-12 — no product impact.
- **Auth target:** NetHub AS issues tokens; NetPay validates. Local password login is transitional only.

## Outstanding issues relevant to current work

- None open after #6 closed.
- Follow-ups recorded in `task.md`.
