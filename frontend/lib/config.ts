/** Runtime public config from NetPay API (no secrets). */

export type SpaConfig = {
  oidc_issuer: string;
  oidc_client_id: string;
  oidc_redirect_uri: string;
  oidc_scopes: string;
  oidc_configured: boolean;
  nethub_api_configured: boolean;
  auth_mode: string;
};

let cached: SpaConfig | null = null;

export function apiBase(): string {
  if (typeof window === "undefined") return "";
  // Same-origin when served by FastAPI; override for local split dev
  const fromEnv = process.env.NEXT_PUBLIC_NETPAY_API_BASE_URL?.replace(/\/$/, "");
  return fromEnv || "";
}

export async function loadSpaConfig(): Promise<SpaConfig> {
  if (cached) return cached;
  const base = apiBase();
  const res = await fetch(`${base}/config.json`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Could not load /config.json");
  }
  cached = (await res.json()) as SpaConfig;
  return cached;
}

export function clearSpaConfigCache(): void {
  cached = null;
}
