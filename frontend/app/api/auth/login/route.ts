import { NextRequest, NextResponse } from "next/server";
import { createAuthorizationRequest, OIDC_TRANSACTION_COOKIE, OIDC_TRANSACTION_TTL_SECONDS } from "../../../../lib/server/oidc";
import { safeReturnTo } from "../../../../lib/server/security.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const returnTo = safeReturnTo(request.nextUrl.searchParams.get("returnTo"), request.nextUrl.origin);
    const login = await createAuthorizationRequest(request.nextUrl.origin, returnTo);
    const response = NextResponse.redirect(login.url);
    response.headers.set("Cache-Control", "no-store");
    response.cookies.set(OIDC_TRANSACTION_COOKIE, login.transactionCookie, {
      httpOnly: true, secure: process.env.NODE_ENV === "production",
      sameSite: "lax", path: "/auth/callback/", maxAge: OIDC_TRANSACTION_TTL_SECONDS,
    });
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login/?error=configuration", request.url));
  }
}
