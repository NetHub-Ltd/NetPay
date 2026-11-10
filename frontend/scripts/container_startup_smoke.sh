#!/usr/bin/env bash
set -Eeuo pipefail

container="netpay-frontend-smoke"
cleanup() { docker rm --force "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$container" -p 127.0.0.1:3000:3000 \
  -e NODE_ENV=production \
  -e NEXT_PUBLIC_SITE_URL=https://pay.example.test \
  ghcr.io/nethub-ltd/netpay-frontend:ci >/dev/null

ready=false
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:3000/ >/dev/null; then
    ready=true
    break
  fi
  if ! docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -qx true; then
    docker logs "$container"
    exit 1
  fi
  sleep 2
done
[[ "$ready" == true ]] || { docker logs "$container"; echo "Next.js did not become healthy"; exit 1; }

curl --fail --silent http://127.0.0.1:3000/login/ | grep -q "Welcome back"
curl --fail --silent http://127.0.0.1:3000/robots.txt | grep -q "Sitemap:"
curl --fail --silent http://127.0.0.1:3000/sitemap.xml | grep -q "<urlset"
curl --fail --silent http://127.0.0.1:3000/api/auth/status | grep -q '"oidc_configured":false'
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/api/backend/v1/auth/me)" = "401"
test "$(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:3000/api/auth/logout)" = "403"

echo "Independent Next.js server, login, SEO routes and BFF boundary passed."
