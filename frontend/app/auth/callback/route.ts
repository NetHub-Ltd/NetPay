import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";
import { exchangeAuthorizationCode, OIDC_TRANSACTION_COOKIE, openTransaction, verifyIdToken } from "../../../lib/server/oidc";
import { createServerSession, SESSION_COOKIE_NAME, sessionCookieOptions, validateHumanAccessToken } from "../../../lib/server/session-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function loginFailure(request: NextRequest, reason: string): NextResponse {
  const response = NextResponse.redirect(new URL("/login/?error=" + reason, request.url));
  response.cookies.set(OIDC_TRANSACTION_COOKIE, "", {
    httpOnly: true, secure: process.env.NODE_ENV === "production",
    sameSite: "lax", path: "/auth/callback/", maxAge: 0,
  });
  return response;
}
function safeReturnTo(value: string, origin: string): string {
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/dashboard/";
  try {
    const parsed = new URL(value, origin);
    return parsed.origin === origin ? parsed.pathname + parsed.search + parsed.hash : "/dashboard/";
  } catch {
    return "/dashboard/";
  }
}
export async function GET(request: NextRequest) {
  if (request.nextUrl.searchParams.has("error")) return loginFailure(request, "provider");
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const tx = openTransaction(request.cookies.get(OIDC_TRANSACTION_COOKIE)?.value);
  if (!code || !state || !tx) return loginFailure(request, "state");
  const supplied = Buffer.from(state);
  const expected = Buffer.from(tx.state);
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) {
    return loginFailure(request, "state");
  }
  try {
    const tokens = await exchangeAuthorizationCode(code, tx.verifier);
    await verifyIdToken(tokens.id_token, tx.nonce);
    await validateHumanAccessToken(tokens.access_token);
    const sessionId = await createServerSession(tokens);
    const response = NextResponse.redirect(new URL(safeReturnTo(tx.returnTo, request.nextUrl.origin), request.url));
    response.cookies.set(SESSION_COOKIE_NAME, sessionId, sessionCookieOptions());
    response.cookies.set(OIDC_TRANSACTION_COOKIE, "", {
      httpOnly: true, secure: process.env.NODE_ENV === "production",
      sameSite: "lax", path: "/auth/callback/", maxAge: 0,
    });
    return response;
  } catch {
    return loginFailure(request, "exchange");
  }
}
