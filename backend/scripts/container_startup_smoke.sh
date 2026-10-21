#!/usr/bin/env bash
set -euo pipefail

image="${1:-ghcr.io/nethub-ltd/netpay:ci}"
name="netpay-startup-smoke"
cleanup() {
  docker logs "$name" || true
  docker stop "$name" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run --detach --rm --name "$name" \
  --add-host=host.docker.internal:host-gateway \
  -p 127.0.0.1:8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql+asyncpg://gateway:gateway@host.docker.internal:5432/gateway \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e SECRET_KEY=ci-only-startup-secret-key-not-for-production \
  -e CREDENTIAL_ENCRYPTION_KEY=MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA= \
  -e PUBLIC_BASE_URL=https://example.invalid \
  "$image"

for attempt in $(seq 1 30); do
  if ! docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null | grep -qx true; then
    echo "Container exited before becoming healthy."
    exit 1
  fi
  if curl --fail --silent --show-error http://127.0.0.1:8000/health/live; then
    echo
    exit 0
  fi
  sleep 2
done

echo "Timed out waiting for /health/live."
exit 1
