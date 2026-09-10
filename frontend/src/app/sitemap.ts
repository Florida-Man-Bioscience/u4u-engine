import type { MetadataRoute } from "next";
import { PRODUCT_LIST, productPath } from "@/lib/products";
import { COMPANY_ORIGIN } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const pages: MetadataRoute.Sitemap = [
    { url: `${COMPANY_ORIGIN}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${COMPANY_ORIGIN}/team`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${COMPANY_ORIGIN}/peptodyssey`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${COMPANY_ORIGIN}/peptodyssey/privacy`, lastModified: now, changeFrequency: "yearly", priority: 0.4 },
  ];
  for (const p of PRODUCT_LIST) {
    pages.push({
      url: `${COMPANY_ORIGIN}${productPath(p.slug)}`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: p.slug === "u4u" || p.slug === "cytogate" ? 0.8 : 0.5,
    });
  }
  return pages;
}
