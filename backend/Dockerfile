# syntax=docker/dockerfile:1

# Build Next.js once as a static export; the runtime does not need Node.js.
FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ARG NEXT_PUBLIC_SITE_URL=https://pay.nethub.co.ke
ENV NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
COPY --from=frontend-build /frontend/out ./app/static
RUN python -m pip install --upgrade pip \
    && python -m pip install . \
    && chown -R app:app /app

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
