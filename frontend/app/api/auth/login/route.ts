import { NextRequest, NextResponse } from "next/server";
import { createAuthorizationRequest, OIDC_TRANSACTION_COOKIE, OIDC_TRANSACTION_TTL_SECONDS } from "../../../../lib/server/oidc";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function safeReturnTo(value: string | null, origin: string): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/dashboard/";
  try {
    const parsed = new URL(value, origin);
    return parsed.origin === origin ? parsed.pathname + parsed.search + parsed.hash : "/dashboard/";
  } catch {
    return "/dashboard/";
  }
}
export async function GET(request: NextRequest) {
  try {
    const returnTo = safeReturnTo(request.nextUrl.searchParams.get("returnTo"), request.nextUrl.origin);
    const login = await createAuthorizationRequest(request.nextUrl.origin, returnTo);
    const response = NextResponse.redirect(login.url);
    response.cookies.set(OIDC_TRANSACTION_COOKIE, login.transactionCookie, {
      httpOnly: true, secure: process.env.NODE_ENV === "production",
      sameSite: "lax", path: "/auth/callback/", maxAge: OIDC_TRANSACTION_TTL_SECONDS,
    });
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login/?error=configuration", request.url));
  }
}
