import { NextResponse } from "next/server";
import { isOidcConfigured } from "../../../../lib/server/security.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const oidcConfigured = isOidcConfigured(process.env);
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
