#!/usr/bin/env bash
set -Eeuo pipefail

# Exercise the production Next.js server as a normal host process, as Vercel does.
# CI intentionally omits OIDC/BFF secrets so readiness must fail closed.
log_file="${TMPDIR:-/tmp}/netpay-next-production-smoke.log"
server_pid=""

cleanup() {
  local exit_code=$?
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  if [[ "$exit_code" -ne 0 ]]; then
    cat "$log_file" || true
  fi
  return "$exit_code"
}
trap cleanup EXIT

npm run start >"$log_file" 2>&1 &
server_pid=$!

ready=false
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:3000/ >/dev/null; then
    ready=true
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    cat "$log_file"
    exit 1
  fi
  sleep 2
done
[[ "$ready" == true ]] || { echo "Next.js production server did not become ready"; exit 1; }

echo "Checking login page"
curl --fail --silent --show-error http://127.0.0.1:3000/login/ | grep -q "Welcome back"

echo "Checking robots and sitemap"
curl --fail --silent --show-error http://127.0.0.1:3000/robots.txt | grep -q "Sitemap:"
curl --fail --silent --show-error http://127.0.0.1:3000/sitemap.xml | grep -q "<urlset"

echo "Checking non-secret OIDC status"
curl --fail --silent --show-error http://127.0.0.1:3000/api/auth/status/ | grep -q '"oidc_configured":false'

echo "Checking fail-closed readiness"
readiness_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3000/api/health/ready/)"
[[ "$readiness_status" == "503" ]]

echo "Checking unauthenticated BFF rejection"
bff_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3000/api/backend/v1/auth/me/)"
[[ "$bff_status" == "401" ]]

echo "Checking logout CSRF protection"
logout_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' -X POST http://127.0.0.1:3000/api/auth/logout/)"
[[ "$logout_status" == "403" ]]

echo "Production Next.js host-process smoke checks passed."
