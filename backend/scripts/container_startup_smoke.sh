#!/usr/bin/env bash
set -euo pipefail

container_name="netpay-bootstrap-smoke"
cleanup() { docker rm --force "$container_name" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run --detach --name "$container_name" --publish 127.0.0.1:8000:8000 ghcr.io/nethub-ltd/netpay:ci
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8000/health/live >/dev/null; then
    curl --fail --silent http://127.0.0.1:8000/health/ready | grep -q '"status":"ok"'
    echo "Container startup smoke test passed."
    exit 0
  fi
  sleep 2
done
echo "NetPay container did not become healthy."
docker logs "$container_name" || true
exit 1
