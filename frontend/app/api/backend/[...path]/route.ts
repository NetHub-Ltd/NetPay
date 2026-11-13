import { NextRequest, NextResponse } from "next/server";
import { backendBaseUrl } from "../../../../lib/server/session-store";
import { resolveAllowedGet } from "../../../../lib/server/security.mjs";
import { getIdpAccessToken } from "../../../../lib/session-token";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function jsonError(status: number, detail: string): NextResponse {
  return NextResponse.json(
    { detail },
    {
      status,
      headers: {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    },
  );
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const upstreamPath = resolveAllowedGet(path, request.nextUrl.searchParams);
  if (!upstreamPath) return jsonError(404, "api_route_not_found");

  const accessToken = await getIdpAccessToken();
  if (!accessToken) {
    return jsonError(401, "authentication_required");
  }

  try {
    const upstream = await fetch(backendBaseUrl() + upstreamPath, {
      headers: {
        Authorization: "Bearer " + accessToken,
        Accept: "application/json",
      },
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(10_000),
    });
    if (upstream.status === 401) {
      return jsonError(401, "session_expired");
    }
    if (upstream.status >= 300 && upstream.status < 400) {
      return jsonError(502, "backend_redirect_rejected");
    }
    if (upstream.status >= 500) {
      return jsonError(502, "backend_request_failed");
    }
    const body =
      upstream.status === 204 || upstream.status === 304 ? null : await upstream.text();
    return new NextResponse(body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") ?? "application/json",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return jsonError(503, "backend_service_unavailable");
  }
}
