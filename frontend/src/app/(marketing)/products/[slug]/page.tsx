import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ProductMarketingPage } from "@/components/ProductMarketingPage";
import {
  PRODUCT_LIST,
  PRODUCTS,
  isProductSlug,
  productCanonical,
  type ProductSlug,
} from "@/lib/products";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return PRODUCT_LIST.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  if (!isProductSlug(slug)) {
    return { title: "Product" };
  }
  const product = PRODUCTS[slug];
  const url = productCanonical(slug);
  return {
    title: product.name,
    description: product.metaDescription,
    alternates: { canonical: url },
    openGraph: {
      title: `${product.name} — Florida Man Bioscience`,
      description: product.metaDescription,
      url,
      siteName: "Florida Man Bioscience",
      type: "website",
      images: product.heroImage
        ? [{ url: product.heroImage.src }]
        : [{ url: "/assets/img/mark.png" }],
    },
  };
}

export default async function ProductSlugPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { slug } = await params;
  if (!isProductSlug(slug)) notFound();
  const product = PRODUCTS[slug as ProductSlug];
  return <ProductMarketingPage product={product} />;
}
