import type { MetadataRoute } from "next";
import { siteUrl } from "../lib/site-url";

export const dynamic = "force-static";

/** Public indexable URLs only. */
export default function sitemap(): MetadataRoute.Sitemap {
  const paths = ["/", "/product/", "/developers/", "/why-netpay/", "/api-overview/", "/faq/", "/request-access/"];

  return paths.map((path) => ({
    url: new URL(path, siteUrl).toString(),
  }));
}
