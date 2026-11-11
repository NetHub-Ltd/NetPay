import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep the normal Next.js server runtime for Route Handlers, the BFF and server-side OIDC.
  // Vercel manages its own deployment output; standalone is only for custom container runtimes.
  trailingSlash: true,
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
