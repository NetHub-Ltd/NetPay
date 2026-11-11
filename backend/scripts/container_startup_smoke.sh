#!/usr/bin/env bash
set -Eeuo pipefail

network="netpay-api-smoke-network"
postgres="netpay-api-smoke-postgres"
redis="netpay-api-smoke-redis"
api="netpay-api-smoke"
# Use one-run credentials; smoke-test secrets must never be committed.
db_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
bff_internal_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
cleanup() {
  docker rm --force "$api" "$postgres" "$redis" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$network" >/dev/null
docker run -d --name "$postgres" --network "$network" \
  -e POSTGRES_USER=netpay -e POSTGRES_PASSWORD="$db_password" -e POSTGRES_DB=netpay postgres:16-alpine >/dev/null
docker run -d --name "$redis" --network "$network" redis:7-alpine >/dev/null

ready=false
for attempt in $(seq 1 30); do
  if docker exec "$postgres" pg_isready -U netpay -d netpay >/dev/null 2>&1 \
    && docker exec "$redis" redis-cli ping 2>/dev/null | grep -qx PONG; then
    ready=true
    break
  fi
  sleep 2
done
[[ "$ready" == true ]] || { echo "Database/cache did not become ready"; exit 1; }

docker run -d --name "$api" --network "$network" -p 127.0.0.1:8000:8000 \
  -e ENVIRONMENT=test \
  -e DB_HOST="$postgres" -e DB_PORT=5432 -e DB_NAME=netpay -e DB_USER=netpay \
  -e DB_PASSWORD="$db_password" -e DB_SSL_MODE=disable -e DB_POOL_SIZE=1 -e DB_MAX_OVERFLOW=0 \
  -e REDIS_URL="redis://$redis:6379/0" -e BFF_INTERNAL_SECRET="$bff_internal_secret" \
  ghcr.io/nethub-ltd/netpay:ci >/dev/null

healthy=false
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8000/health/live >/dev/null; then
    healthy=true
    break
  fi
  if ! docker inspect -f '{{.State.Running}}' "$api" 2>/dev/null | grep -qx true; then
    docker logs "$api"
    exit 1
  fi
  sleep 2
done
[[ "$healthy" == true ]] || { docker logs "$api"; echo "API did not become healthy"; exit 1; }

curl --fail --silent http://127.0.0.1:8000/health/ready | grep -q '"database":"ok"'
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)" = "404"
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/config.json)" = "404"
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/v1/auth/me)" = "401"
test "$(curl -s -o /dev/null -w '%{http_code}' -H 'X-NetPay-BFF-Secret: wrong' http://127.0.0.1:8000/internal/v1/bff/sessions/ready)" = "401"

echo "Independent API container, health checks and browser/auth boundaries passed."
