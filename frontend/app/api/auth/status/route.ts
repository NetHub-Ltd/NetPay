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
  const bffConfigured = Boolean(
    process.env.NETPAY_BACKEND_INTERNAL_URL &&
    process.env.BFF_INTERNAL_SECRET &&
    process.env.BFF_INTERNAL_SECRET.length >= 32,
  );
  return NextResponse.json(
    { oidc_configured: oidcConfigured, bff_configured: bffConfigured },
    { headers: { "Cache-Control": "no-store" } },
  );
}
