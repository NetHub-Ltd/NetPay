# Repository State

**Last updated:** 2026-09-15

| Field | Value |
|-------|--------|
| Repository | https://github.com/NetHub-Ltd/NetPay.git |
| Default branch | `main` (protected) |
| Integration branch | `dev` — **all PRs target `dev`** |
| Preferred deploy | k3s (later); current host Render + CF edge |

## GitHub milestones (Production Readiness Gate)

| Milestone | State | Notes |
|-----------|--------|--------|
| **M0 — Baseline** | **closed** | 6/6 issues closed |
| **P0 — Financial integrity** | **closed** | Blocking GO complete |
| **P1 — Collections & async durability** | **closed** | #24 C2B closed (PR #57) |
| **P2 — Security & operations** | **open** | Next: #25 NetHub AS |
| **P3 — Expand rails** | **open** | Refunds / B2C / providers |

## Recent product work on `dev` (post-gate)

- Redis live bus + Layout WebSocket + toasts
- DataTable + payment lifecycle labels
- STK harden (ResultDesc, query-provider)
- C2B confirmation → canonical payment (#24)
- Payment detail polish, notif drawer
