import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async redirects() {
    return [
      // Common App Store / human guesses for the privacy policy
      {
        source: "/privacy",
        destination: "/peptodyssey/privacy",
        permanent: true,
      },
      {
        source: "/privacy/",
        destination: "/peptodyssey/privacy",
        permanent: true,
      },
      {
        source: "/peptodyssey/privacy-policy",
        destination: "/peptodyssey/privacy",
        permanent: true,
      },
      // Legacy product home was apex `/` (genome upload). New product entry is the hub;
      // the upload tool lives at /peptodyssey/analyze. Bookmark helpers:
      {
        source: "/analyze",
        destination: "/peptodyssey/analyze",
        permanent: true,
      },
      {
        source: "/analyze/",
        destination: "/peptodyssey/analyze",
        permanent: true,
      },
      {
        source: "/upload",
        destination: "/peptodyssey/analyze",
        permanent: true,
      },
      {
        source: "/new",
        destination: "/peptodyssey/analyze",
        permanent: true,
      },
    ];
  },
  async rewrites() {
    const owui =
      process.env.OWUI_UPSTREAM ?? "http://lab-chat.theswamp.svc:8080";
    return [
      { source: "/owui", destination: `${owui}/owui` },
      { source: "/owui/:path*", destination: `${owui}/owui/:path*` },
    ];
  },
};

export default nextConfig;
