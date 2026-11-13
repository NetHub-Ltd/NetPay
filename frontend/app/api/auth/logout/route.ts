import { NextRequest, NextResponse } from "next/server";
import { signOut } from "../../../../auth";
import { isSameOriginRequest } from "../../../../lib/server/security.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  if (
    !isSameOriginRequest(
      request.headers.get("origin"),
      request.nextUrl.origin,
      request.headers.get("sec-fetch-site"),
    )
  ) {
    return NextResponse.json({ detail: "csrf_check_failed" }, { status: 403 });
  }
  try {
    await signOut({ redirect: false });
  } catch {
    return NextResponse.json({ detail: "logout_unavailable" }, { status: 503 });
  }
  return new NextResponse(null, {
    status: 204,
    headers: { "Cache-Control": "no-store" },
  });
}
