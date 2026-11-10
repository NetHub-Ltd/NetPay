import { NextRequest, NextResponse } from "next/server";
import { expiredSessionCookieOptions, getSessionFromRequest, revokeServerSession, SESSION_COOKIE_NAME } from "../../../../lib/server/session-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin !== request.nextUrl.origin || request.headers.get("sec-fetch-site") === "cross-site") {
    return NextResponse.json({ detail: "csrf_check_failed" }, { status: 403 });
  }
  try {
    const current = await getSessionFromRequest(request);
    if (current) await revokeServerSession(current.sessionId);
  } catch {
    return NextResponse.json({ detail: "logout_unavailable" }, { status: 503 });
  }
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE_NAME, "", expiredSessionCookieOptions());
  return response;
}
