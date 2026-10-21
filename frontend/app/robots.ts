import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // Let crawlers read dashboard metadata; its page-level noindex is authoritative.
        disallow: ["/api/", "/docs", "/openapi.json", "/health/"],
      },
    ],
    sitemap: new URL("/sitemap.xml", siteUrl).toString(),
  };
}
