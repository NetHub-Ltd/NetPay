#!/usr/bin/env bash
set -Eeuo pipefail

# Exercise the production Next.js server as a normal host process, as Vercel does.
# CI intentionally omits OIDC/BFF secrets so readiness must fail closed.
log_file="$(mktemp "${TMPDIR:-/tmp}/netpay-next-production-smoke.XXXXXX")"
server_pid=""
server_port="${PORT:-$(node -e 'const net = require("node:net"); const server = net.createServer(); server.listen(0, "127.0.0.1", () => { const address = server.address(); if (address && typeof address !== "string") console.log(address.port); server.close(); });')}"
server_url="http://127.0.0.1:${server_port}"
site_origin="${NEXT_PUBLIC_SITE_URL:-https://netpay.nethub.co.ke}"
site_origin="${site_origin%/}"
export AUTH_SECRET="$(node -p 'require("node:crypto").randomBytes(32).toString("base64url")')"
export AUTH_URL="$server_url"

cleanup() {
  local exit_code=$?
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  if [[ "$exit_code" -ne 0 ]]; then
    cat "$log_file" || true
  fi
  rm -f "$log_file"
  return "$exit_code"
}
trap cleanup EXIT

./node_modules/.bin/next start --hostname 127.0.0.1 --port "$server_port" >"$log_file" 2>&1 &
server_pid=$!

ready=false
for attempt in $(seq 1 30); do
  if curl --fail --silent "$server_url/" >/dev/null; then
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
curl --fail --silent --show-error "$server_url/login/" | grep -q "Welcome back"

echo "Checking canonical, robots and sitemap origins"
homepage_html="$(curl --fail --silent --show-error "$server_url/")"
grep -Fq "<link rel=\"canonical\" href=\"${site_origin}/\"" <<<"$homepage_html"
robots_txt="$(curl --fail --silent --show-error "$server_url/robots.txt")"
grep -Fq "Sitemap: ${site_origin}/sitemap.xml" <<<"$robots_txt"
sitemap_xml="$(curl --fail --silent --show-error "$server_url/sitemap.xml")"
grep -Fq "<urlset" <<<"$sitemap_xml"
grep -Fq "<loc>${site_origin}/</loc>" <<<"$sitemap_xml"

echo "Checking non-secret OIDC status"
curl --fail --silent --show-error "$server_url/api/auth/status/" | grep -q '"oidc_configured":false'

echo "Checking fail-closed readiness"
readiness_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$server_url/api/health/ready/")"
[[ "$readiness_status" == "503" ]]

echo "Checking unauthenticated BFF rejection"
bff_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$server_url/api/backend/v1/auth/me/")"
[[ "$bff_status" == "401" ]]

echo "Checking logout CSRF protection"
logout_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' -X POST "$server_url/api/auth/logout/")"
[[ "$logout_status" == "403" ]]

echo "Production Next.js host-process smoke checks passed."
