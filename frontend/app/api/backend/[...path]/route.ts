import { NextRequest, NextResponse } from "next/server";
import { getSessionFromRequest, revokeServerSession, SESSION_COOKIE_NAME, expiredSessionCookieOptions } from "../../../../lib/server/session-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function resolveAllowedGet(path: string[], request: NextRequest): string | null {
  const route = path.join("/");
  if (route === "v1/auth/me" || route === "v1/auth/memberships") return "/api/" + route;
  const merchant = route.match(/^v1\/auth\/merchants\/([^/]+)$/);
  if (merchant && UUID.test(merchant[1])) return "/api/v1/auth/merchants/" + merchant[1];
  const payments = route.match(/^v1\/auth\/merchants\/([^/]+)\/payments$/);
  if (payments && UUID.test(payments[1])) {
    if ([...request.nextUrl.searchParams.keys()].some((key) => key !== "limit")) return null;
    const raw = request.nextUrl.searchParams.get("limit") ?? "20";
    if (!/^\d{1,3}$/.test(raw)) return null;
    const limit = Number(raw);
    if (limit < 1 || limit > 100) return null;
    return "/api/v1/auth/merchants/" + payments[1] + "/payments?limit=" + limit;
  }
  return null;
}
function jsonError(status: number, detail: string): NextResponse {
  return NextResponse.json({ detail }, { status, headers: {
    "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
  } });
}
export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const upstreamPath = resolveAllowedGet(path, request);
  if (!upstreamPath) return jsonError(404, "api_route_not_found");
  let current: Awaited<ReturnType<typeof getSessionFromRequest>>;
  try {
    current = await getSessionFromRequest(request);
  } catch {
    return jsonError(503, "session_service_unavailable");
  }
  if (!current) {
    const response = jsonError(401, "authentication_required");
    response.cookies.set(SESSION_COOKIE_NAME, "", expiredSessionCookieOptions());
    return response;
  }
  const base = process.env.NETPAY_BACKEND_INTERNAL_URL?.trim().replace(/\/+$/, "");
  if (!base) return jsonError(503, "backend_service_unavailable");
  try {
    const upstream = await fetch(base + upstreamPath, {
      headers: { Authorization: "Bearer " + current.session.access_token, Accept: "application/json" },
      cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(10_000),
    });
    if (upstream.status === 401) {
      await revokeServerSession(current.sessionId);
      const response = jsonError(401, "session_expired");
      response.cookies.set(SESSION_COOKIE_NAME, "", expiredSessionCookieOptions());
      return response;
    }
    if (upstream.status >= 500) return jsonError(502, "backend_request_failed");
    return new NextResponse(await upstream.text(), { status: upstream.status, headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
    } });
  } catch {
    return jsonError(503, "backend_service_unavailable");
  }
}
