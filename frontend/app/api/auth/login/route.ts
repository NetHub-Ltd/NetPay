import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** Legacy entry point — human login is Auth.js public OIDC. */
export async function GET(request: NextRequest) {
  const url = new URL("/api/auth/signin/oidc", request.url);
  url.searchParams.set("callbackUrl", "/dashboard/");
  return NextResponse.redirect(url);
}
