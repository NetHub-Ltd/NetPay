import { NextRequest, NextResponse } from "next/server";
import { getSessionFromRequest, revokeServerSession, SESSION_COOKIE_NAME, expiredSessionCookieOptions } from "../../../../lib/server/session-store";
import { resolveAllowedGet } from "../../../../lib/server/security.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function jsonError(status: number, detail: string): NextResponse {
  return NextResponse.json({ detail }, { status, headers: {
    "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
  } });
}
export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const upstreamPath = resolveAllowedGet(path, request.nextUrl.searchParams);
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
