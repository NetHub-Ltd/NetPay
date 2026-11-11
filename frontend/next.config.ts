import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A server runtime is required for Route Handlers, the BFF and server-side OIDC.
  output: "standalone",
  trailingSlash: true,
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
