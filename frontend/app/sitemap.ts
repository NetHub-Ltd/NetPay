import type { MetadataRoute } from "next";
import { siteUrl } from "../lib/site-url";

export const dynamic = "force-static";

/** Public indexable URLs only. */
export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();

  const paths = ["/", "/product/", "/developers/", "/why-netpay/", "/api-overview/", "/faq/", "/request-access/"];

  return paths.map((path, i) => ({
    url: new URL(path, siteUrl).toString(),
    lastModified,
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : ["/product/", "/developers/", "/why-netpay/"].includes(path) ? 0.85 : 0.7 - i * 0.03,
  }));
}
