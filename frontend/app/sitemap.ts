import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

  return [
    {
      url: new URL("/", siteUrl).toString(),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
