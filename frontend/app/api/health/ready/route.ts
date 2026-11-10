import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const oidcConfigured = Boolean(
    process.env.OIDC_ISSUER &&
    process.env.OIDC_CLIENT_ID &&
    process.env.OIDC_CLIENT_SECRET &&
    process.env.OIDC_REDIRECT_URI &&
    process.env.OIDC_TRANSACTION_SECRET,
  );
  let backendBase = "";
  try {
    const backendUrl = new URL(process.env.NETPAY_BACKEND_INTERNAL_URL ?? "");
    if (backendUrl.username || backendUrl.password || backendUrl.search || backendUrl.hash || backendUrl.pathname !== "/") {
      throw new Error("Invalid backend origin");
    }
    backendBase = backendUrl.origin;
  } catch {
    backendBase = "";
  }
  const bffSecret = process.env.BFF_INTERNAL_SECRET;
  if (!oidcConfigured || !backendBase || !bffSecret) {
    return NextResponse.json(
      { status: "not_ready", oidc_configured: oidcConfigured, bff_configured: false },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  try {
    const [api, sessionStore] = await Promise.all([
      fetch(backendBase + "/health/ready", {
        cache: "no-store", redirect: "error", signal: AbortSignal.timeout(4_000),
      }),
      fetch(backendBase + "/internal/v1/bff/sessions/ready", {
        headers: { "X-NetPay-BFF-Secret": bffSecret },
        cache: "no-store", signal: AbortSignal.timeout(4_000),
      }),
    ]);
    if (!api.ok || !sessionStore.ok) {
      return NextResponse.json(
        { status: "not_ready", oidc_configured: true, bff_configured: true },
        { status: 503, headers: { "Cache-Control": "no-store" } },
      );
    }
    return NextResponse.json(
      { status: "ok", oidc_configured: true, bff_configured: true },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return NextResponse.json(
      { status: "not_ready", oidc_configured: true, bff_configured: false },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
