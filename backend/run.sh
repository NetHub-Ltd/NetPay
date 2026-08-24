#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || cp .env.example .env
mkdir -p data static
if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev 2>/dev/null || uv pip install -e ".[dev]"
else
  pip install -e ".[dev]"
fi
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/gateway.db}"
export REDIS_REQUIRED="${REDIS_REQUIRED:-false}"
export STATIC_DIR="${STATIC_DIR:-$(pwd)/static}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
