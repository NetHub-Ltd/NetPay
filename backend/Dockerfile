# syntax=docker/dockerfile:1

# --- Frontend build (SPA → dist/) ---
# OIDC_* build-args mirror NetHubKe naming; mapped to VITE_* for the SPA bundle.
# Set in CI from GitHub vars/secrets (e.g. OIDC_ISSUER, OIDC_CLIENT_ID).
# SPA is a public client (PKCE) — do NOT pass OIDC_CLIENT_SECRET into the browser build.
FROM node:22-alpine AS frontend-build
WORKDIR /fe
ENV npm_config_registry=https://registry.npmjs.org/

ARG OIDC_ISSUER=https://build-placeholder.invalid
ARG OIDC_CLIENT_ID=build-placeholder-client
ARG OIDC_REDIRECT_URI=
ARG OIDC_SCOPES=openid profile email offline_access

ENV VITE_OIDC_ISSUER=$OIDC_ISSUER \
    VITE_OIDC_CLIENT_ID=$OIDC_CLIENT_ID \
    VITE_OIDC_REDIRECT_URI=$OIDC_REDIRECT_URI \
    VITE_OIDC_SCOPES=$OIDC_SCOPES

COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run lint && npm run build \
 && test -f dist/index.html

# --- Python deps ---
FROM python:3.12-slim AS builder
WORKDIR /build
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
RUN pip install --no-cache-dir uv \
 && uv pip install --system --no-cache .

# --- Runtime: API + static dashboard ---
FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 10001 gateway \
 && mkdir -p /app/data /app/static /app/logs \
 && chown -R gateway:gateway /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY --from=frontend-build /fe/dist/ ./static/

RUN chown -R gateway:gateway /app/static

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    LOG_DIR=/app/logs \
    STATIC_DIR=/app/static

USER gateway
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
