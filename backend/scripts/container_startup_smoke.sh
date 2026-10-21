#!/usr/bin/env bash
set -euo pipefail

network="netpay-smoke-network"
postgres="netpay-smoke-postgres"
redis="netpay-smoke-redis"
api="netpay-bootstrap-smoke"
cleanup() {
  docker rm --force "$api" "$postgres" "$redis" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$network" >/dev/null
docker run --detach --name "$postgres" --network "$network" \
  --env POSTGRES_USER=netpay --env POSTGRES_PASSWORD=netpay --env POSTGRES_DB=netpay postgres:16-alpine >/dev/null
docker run --detach --name "$redis" --network "$network" redis:7-alpine >/dev/null
for attempt in $(seq 1 30); do
  if docker exec "$postgres" pg_isready -U netpay -d netpay >/dev/null 2>&1 \
    && docker exec "$redis" redis-cli ping | grep -qx PONG; then
    break
  fi
  sleep 2
done
docker exec "$postgres" pg_isready -U netpay -d netpay >/dev/null
docker exec "$redis" redis-cli ping | grep -qx PONG

docker run --detach --name "$api" --network "$network" --publish 127.0.0.1:8000:8000 \
  --env ENVIRONMENT=test \
  --env DATABASE_URL=postgresql+asyncpg://netpay:netpay@netpay-smoke-postgres:5432/netpay \
  --env REDIS_URL=redis://netpay-smoke-redis:6379/0 \
  ghcr.io/nethub-ltd/netpay:ci >/dev/null
for attempt in $(seq 1 30); do
  if docker logs "$api" 2>&1 | grep -q 'database_connectivity=ok'; then
    if curl --fail --silent http://127.0.0.1:8000/health/live >/dev/null; then
      curl --fail --silent http://127.0.0.1:8000/health/ready | grep -q '"database":"ok"'
      curl --fail --silent --show-error http://127.0.0.1:8000/ | grep -q "NetPay"
      curl --fail --silent --show-error http://127.0.0.1:8000/dashboard/ | grep -q "Merchant dashboard preview"
      curl --fail --silent --show-error http://127.0.0.1:8000/robots.txt | grep -q "Sitemap:"
      curl --fail --silent --show-error http://127.0.0.1:8000/sitemap.xml | grep -q "<urlset"
      echo "Container startup, health endpoints, and frontend static routes passed."
      exit 0
    fi
  fi
  if ! docker inspect -f '{{.State.Running}}' "$api" 2>/dev/null | grep -qx true; then
    docker logs "$api" || true
    exit 1
  fi
  sleep 2
done
echo "NetPay container did not become healthy."
docker logs "$api" || true
exit 1
