import { NextRequest, NextResponse } from "next/server";
import { exchangeAuthorizationCode, OIDC_TRANSACTION_COOKIE, openTransaction, verifyIdToken } from "../../../lib/server/oidc";
import { constantTimeEqual, safeReturnTo } from "../../../lib/server/security.mjs";
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
export async function GET(request: NextRequest) {
  if (request.nextUrl.searchParams.has("error")) return loginFailure(request, "provider");
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const tx = openTransaction(request.cookies.get(OIDC_TRANSACTION_COOKIE)?.value);
  if (!code || !state || !tx) return loginFailure(request, "state");
  if (!constantTimeEqual(state, tx.state)) {
    return loginFailure(request, "state");
  }
  try {
    const tokens = await exchangeAuthorizationCode(code, tx.verifier);
    await verifyIdToken(tokens.id_token, tx.nonce, undefined, tokens.access_token);
    await validateHumanAccessToken(tokens.access_token);
    const sessionId = await createServerSession(tokens);
    const response = NextResponse.redirect(new URL(safeReturnTo(tx.returnTo, request.nextUrl.origin), request.url));
    response.headers.set("Cache-Control", "no-store");
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
