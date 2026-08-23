# Progress

## 2026-08-23 — React dashboard (Vite) integrated

- Vite + React + TypeScript SPA under `frontend/`
- Screens: Login, Health, Tenants, Tenant detail, Integrations, Integration detail (C2B register), Webhooks, Payment intents, Intent detail, Event log (replay), OAuth clients, 403, 404
- JWT auth via sessionStorage; role-gated nav (admin vs user)
- `npm run build` → `frontend/dist`; FastAPI serves `/` + `/assets` + SPA fallback
- Dev: `npm run dev` on :5173 with proxy to API :8000
- Playwright walkthrough screenshots: `artifacts/screenshots/01-login.png` … `14-not-found.png`

## Backend acceptance (prior)

- Admin bootstrap, Alembic, dual DB URLs, STK/C2B, webhook liveness ≤3, internal API key, health probes, uv
