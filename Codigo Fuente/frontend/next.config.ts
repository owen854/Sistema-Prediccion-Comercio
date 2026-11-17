import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Imagen mínima para Docker (infra/docker/web.Dockerfile).
  output: "standalone",
  reactStrictMode: true,
};

export default nextConfig;
