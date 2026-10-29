# NetPay deployment notes

## Docker Compose

1. Copy `backend/.env.example` to `backend/.env` and generate a real `SECRET_KEY` and `CREDENTIAL_ENCRYPTION_KEY`.
2. Set `PUBLIC_BASE_URL` to a publicly reachable HTTPS origin for Daraja callbacks (for local sandbox work, use a secure tunnel URL rather than `localhost`).
3. Run `docker compose -f deploy/docker-compose.yml up --build` from the repository root. Compose waits for PostgreSQL, runs the one-shot Alembic migration service, then starts the API and the durable event worker.

The public landing page is a static Next.js export served by FastAPI. API routes and callback routes share the same origin.

## Kubernetes

The secret `nethub-gateway-secrets` must contain at least:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DB_SSL_MODE` — separate PostgreSQL connection settings; use `DB_SSL_MODE=require` for Aiven TLS. The application builds asyncpg and Alembic psycopg URLs internally.
- `SECRET_KEY` — random string of at least 32 characters
- `CREDENTIAL_ENCRYPTION_KEY` — valid Fernet key
- `PUBLIC_BASE_URL` — public HTTPS origin, e.g. `https://pay.nethub.co.ke`
- `CORS_ORIGINS` — optional comma-separated origins if browser clients need cross-origin API access

For each release, run the migration Job once before rolling out API/worker pods:

```bash
kubectl delete job nethub-gateway-migrate --ignore-not-found
kubectl apply -f deploy/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/nethub-gateway-migrate --timeout=180s
kubectl apply -f deploy/k8s/deployment.yaml
```

The API liveness probe checks `/health/live`; readiness checks `/health/ready`. A database outage should remove pods from service without triggering liveness restarts. The worker uses PostgreSQL row locking and durable retry timestamps; it is deployed separately from API replicas.

PostgreSQL remains authoritative for payment state, callback deduplication, idempotency, outbox events, and delivery attempts.

## Important rollout boundary

The Next.js dashboard route is currently a no-index placeholder, not an authenticated merchant console. The M2M API and callback pipeline are the implemented integration surface. Do not expose merchant data in the dashboard until NetHub identity/session integration is completed.
