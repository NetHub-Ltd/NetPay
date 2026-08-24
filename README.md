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

## Container (GHCR)

Images: `ghcr.io/nethub-ltd/netpay`

| Ref | Tags |
|-----|------|
| `main` branch | `main`, `sha-<short>` |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `latest` |

```bash
# from repo root — builds SPA into /app/static inside the image
docker build -f backend/Dockerfile -t netpay:local .

docker run --rm -p 8000:8000 \
  -e DATABASE_URL=sqlite+aiosqlite:///./data/gateway.db \
  -e REDIS_REQUIRED=false \
  -e SECRET_KEY=dev \
  netpay:local
# API + dashboard: http://localhost:8000
# Health: http://localhost:8000/health
```

CI pushes to GHCR after tests pass on `main` and on version tags (`v*`).

