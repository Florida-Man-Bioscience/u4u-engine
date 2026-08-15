import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";
import {
  PRODUCT_LIST,
  productPath,
  type ProductPage,
} from "@/lib/products";

type Props = {
  product: ProductPage;
};

export function ProductMarketingPage({ product }: Props) {
  const others = PRODUCT_LIST.filter((p) => p.slug !== product.slug);

  return (
    <CompanyChrome active="products">
      <main>
        {/* Hero */}
        <section
          className="border-b border-[#edecea]"
          style={{ background: `linear-gradient(180deg, ${product.accent.wash} 0%, #ffffff 72%)` }}
        >
          <div className="mx-auto grid max-w-[1180px] gap-10 px-6 py-14 md:grid-cols-2 md:items-center md:px-7 md:py-20">
            <div>
              <p
                className="mb-3 text-xs font-bold uppercase tracking-[0.14em]"
                style={{ color: product.accent.label }}
              >
                {product.eyebrow}
              </p>
              <h1
                className="text-4xl leading-tight text-[#0d1117] md:text-5xl"
                style={companySerif}
              >
                {product.name}
              </h1>
              <p
                className="mt-3 text-xl leading-snug text-[#0d1117]/90 md:text-2xl"
                style={companySerif}
              >
                {product.tagline}
              </p>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-[#3a3f4a]">
                {product.description}
              </p>
              <p className="mt-4 max-w-xl text-sm leading-relaxed text-[#6b7280]">
                <span className="font-semibold text-[#3a3f4a]">Who it’s for. </span>
                {product.audience}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={product.ctaPrimary.href}
                  className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
                  style={{ backgroundColor: product.accent.solid }}
                >
                  {product.ctaPrimary.label} <span aria-hidden>→</span>
                </a>
                <Link
                  href={product.ctaSecondary.href}
                  className="inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] bg-white px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
                >
                  {product.ctaSecondary.label}
                </Link>
              </div>
              <p className="mt-5 max-w-lg text-xs leading-relaxed text-[#6b7280]">
                <span className="font-medium text-[#3a3f4a]">Status: </span>
                {product.statusNote}
              </p>
            </div>

            <div className="relative">
              {product.heroImage ? (
                <div className="overflow-hidden rounded-2xl border border-[#dbd9d3] bg-white shadow-[0_20px_50px_-28px_rgba(13,17,23,0.35)]">
                  <picture>
                    {product.heroImage.webp ? (
                      <source type="image/webp" srcSet={product.heroImage.webp} />
                    ) : null}
                    <img
                      src={product.heroImage.src}
                      alt={product.heroImage.alt}
                      width={1000}
                      height={750}
                      className="h-full w-full object-cover"
                      fetchPriority="high"
                    />
                  </picture>
                </div>
              ) : (
                <div
                  className="flex min-h-[280px] flex-col justify-between overflow-hidden rounded-2xl border border-[#dbd9d3] p-8 shadow-[0_20px_50px_-28px_rgba(13,17,23,0.35)] md:min-h-[340px]"
                  style={{
                    background: `radial-gradient(120% 90% at 10% 10%, #fff 0%, ${product.accent.wash} 45%, #fff 100%)`,
                  }}
                >
                  <div>
                    <p
                      className="text-xs font-bold uppercase tracking-[0.16em]"
                      style={{ color: product.accent.label }}
                    >
                      {product.tag}
                    </p>
                    <p
                      className="mt-6 max-w-sm text-3xl leading-tight text-[#0d1117]"
                      style={companySerif}
                    >
                      {product.tagline}
                    </p>
                  </div>
                  <div className="mt-10 flex flex-wrap gap-2">
                    {product.promises.slice(0, 2).map((p) => (
                      <span
                        key={p}
                        className="rounded-full border border-[#dbd9d3]/80 bg-white/80 px-3 py-1 text-xs font-medium text-[#3a3f4a] backdrop-blur"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Pillars */}
        <section className="border-b border-[#edecea] py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p
              className="text-xs font-bold uppercase tracking-[0.14em]"
              style={{ color: product.accent.label }}
            >
              Why it matters
            </p>
            <h2
              className="mt-2 max-w-2xl text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Marketing that stays honest.
            </h2>
            <div className="mt-10 grid gap-5 md:grid-cols-3">
              {product.pillars.map((pillar) => (
                <article
                  key={pillar.title}
                  className="rounded-2xl border border-[#dbd9d3] bg-white p-6 shadow-[0_1px_0_rgba(13,17,23,0.04)]"
                >
                  <div
                    className="mb-4 h-1 w-10 rounded-full"
                    style={{ backgroundColor: product.accent.solid }}
                    aria-hidden
                  />
                  <h3 className="text-lg text-[#0d1117]" style={companySerif}>
                    {pillar.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                    {pillar.body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Promises + disclaimer */}
        <section className="border-b border-[#edecea] bg-[#f5f4f0] py-16 md:py-20">
          <div className="mx-auto grid max-w-[1180px] gap-10 px-6 md:grid-cols-[1.1fr_0.9fr] md:px-7">
            <div>
              <p
                className="text-xs font-bold uppercase tracking-[0.14em]"
                style={{ color: product.accent.label }}
              >
                What you can expect
              </p>
              <h2
                className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
                style={companySerif}
              >
                Clear commitments. No theater.
              </h2>
              <ul className="mt-8 space-y-3">
                {product.promises.map((item) => (
                  <li
                    key={item}
                    className="flex gap-3 rounded-xl border border-[#dbd9d3] bg-white px-4 py-3 text-sm text-[#3a3f4a]"
                  >
                    <span
                      className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-bold text-white"
                      style={{ backgroundColor: product.accent.solid }}
                      aria-hidden
                    >
                      ✓
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <aside className="rounded-2xl border border-[#dbd9d3] bg-white p-6 md:p-8">
              <h3 className="text-lg text-[#0d1117]" style={companySerif}>
                Important note
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#3a3f4a]">
                {product.disclaimer}
              </p>
              {product.portfolioOrigin ? (
                <p className="mt-5 text-sm text-[#6b7280]">
                  Portfolio host:{" "}
                  <a
                    href={`${product.portfolioOrigin}/`}
                    className="font-medium hover:underline"
                    style={{ color: product.accent.solid }}
                    rel="noopener noreferrer"
                  >
                    {product.portfolioOrigin.replace(/^https?:\/\//, "")}
                  </a>
                </p>
              ) : null}
              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  href={product.ctaPrimary.href}
                  className="inline-flex rounded-full px-4 py-2 text-sm font-semibold text-white"
                  style={{ backgroundColor: product.accent.solid }}
                >
                  {product.ctaPrimary.label}
                </a>
                <Link
                  href="/#products"
                  className="inline-flex rounded-full border border-[#dbd9d3] px-4 py-2 text-sm font-semibold text-[#0d1117]"
                >
                  All programs
                </Link>
              </div>
            </aside>
          </div>
        </section>

        {/* Other products */}
        <section className="py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
              More from Florida Man Bioscience
            </p>
            <h2
              className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Explore the portfolio.
            </h2>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {others.map((p) => (
                <Link
                  key={p.slug}
                  href={productPath(p.slug)}
                  className="group rounded-2xl border border-[#dbd9d3] bg-white p-5 transition hover:border-[#1a6b4a]/35 hover:shadow-[0_12px_30px_-20px_rgba(13,17,23,0.45)]"
                >
                  <p
                    className="text-[11px] font-bold uppercase tracking-[0.12em]"
                    style={{ color: p.accent.label }}
                  >
                    {p.tag}
                  </p>
                  <h3
                    className="mt-2 text-lg text-[#0d1117] group-hover:text-[#1a6b4a]"
                    style={companySerif}
                  >
                    {p.name}
                  </h3>
                  <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-[#3a3f4a]">
                    {p.cardBody}
                  </p>
                  <span className="mt-3 inline-block text-sm font-medium text-[#1a6b4a]">
                    View page →
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </main>
    </CompanyChrome>
  );
}
