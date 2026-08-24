# NetHub Payment Gateway (NetPay)

Multi-tenant M-Pesa payment gateway — FastAPI backend + React dashboard.

## Layout

```text
backend/     FastAPI app, Alembic, tests, static/ (SPA build output)
frontend/    Vite + React source
deploy/      docker-compose, k8s
scripts/     helper scripts (e.g. build-frontend.sh)
```

## Backend

```bash
cd backend
cp .env.example .env
./run.sh
# API: http://127.0.0.1:8000  docs: /docs
```

Tests:

```bash
cd backend
pip install -e ".[dev]"
pytest -q
```

## Frontend (dev)

```bash
cd frontend
npm ci
npm run dev    # http://127.0.0.1:5173 (proxies API to :8000)
```

## SPA into FastAPI static

```bash
./scripts/build-frontend.sh   # lint + build → backend/static/
# then start backend; it serves backend/static at / and /assets
```

Or set `STATIC_DIR` to any folder containing `index.html` + `assets/`.

## Docker

```bash
# from repo root
docker compose -f deploy/docker-compose.yml up --build
```

Build context is the repo root (`backend/Dockerfile` copies frontend + backend).

## CI

PRs to `main` run backend pytest and frontend lint + build. Prefer merging only when checks are green.
