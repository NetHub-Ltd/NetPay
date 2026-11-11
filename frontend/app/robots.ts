import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/api/",
          "/docs",
          "/openapi.json",
          "/health/",
          "/dashboard",
          "/dashboard/",
          "/theme",
          "/theme/",
          "/theme-test",
          "/theme-test/",
        ],
      },
    ],
    sitemap: new URL("/sitemap.xml", siteUrl).toString(),
    host: siteUrl,
  };
}
