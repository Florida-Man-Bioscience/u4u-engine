import type { MetadataRoute } from "next";
import { COMPANY_ORIGIN } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${COMPANY_ORIGIN}/sitemap.xml`,
    host: COMPANY_ORIGIN,
  };
}
