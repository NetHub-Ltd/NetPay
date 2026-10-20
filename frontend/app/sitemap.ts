import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";
  return [{ url: baseUrl, changeFrequency: "weekly", priority: 1 }];
}
