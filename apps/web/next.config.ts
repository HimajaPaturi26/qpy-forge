import type { NextConfig } from "next";

const apiOrigin = process.env.Q2PY_API_ORIGIN ?? "http://127.0.0.1:43118";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
