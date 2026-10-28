import type { MetadataRoute } from "next";

export const dynamic = "force-static";

/**
 * Public indexable URLs only. Dashboard is intentionally omitted (page-level noindex).
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";
  const lastModified = new Date("2026-10-28");

  return [
    {
      url: new URL("/", siteUrl).toString(),
      lastModified,
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
