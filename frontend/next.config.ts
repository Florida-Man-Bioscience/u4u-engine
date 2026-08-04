import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Soft bookmarks: root used to be the genome upload tool. Prefer hub/analyze;
  // do not 301 `/` itself (company home owns it).
  async redirects() {
    return [
      {
        source: "/analyze",
        destination: "/peptodyssey/analyze",
        permanent: true,
      },
      {
        source: "/privacy",
        destination: "/peptodyssey/privacy",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
