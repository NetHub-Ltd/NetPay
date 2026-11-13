import { NextResponse } from "next/server";
import { auth } from "../../../../auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function present(name: string): boolean {
  const value = process.env[name];
  return typeof value === "string" && value.trim().length > 0;
}

export async function GET() {
  const oidcConfigured =
    present("AUTH_OIDC_ISSUER") &&
    present("AUTH_OIDC_CLIENT_ID") &&
    present("AUTH_SECRET") &&
    present("AUTH_URL");

  const bffConfigured = Boolean(
    process.env.NETPAY_BACKEND_INTERNAL_URL &&
      process.env.NETPAY_BACKEND_INTERNAL_URL.trim().length > 0,
  );

  const session = await auth().catch(() => null);

  return NextResponse.json(
    {
      oidc_configured: oidcConfigured,
      bff_configured: bffConfigured,
      authjs: true,
      public_client: true,
      signed_in: Boolean(session?.hasAccessToken),
      checks: {
        auth_secret_present: present("AUTH_SECRET"),
        auth_url_present: present("AUTH_URL"),
        issuer_present: present("AUTH_OIDC_ISSUER"),
        client_id_present: present("AUTH_OIDC_CLIENT_ID"),
        /** Public client: secret must not be required */
        client_secret_not_required: true,
      },
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
