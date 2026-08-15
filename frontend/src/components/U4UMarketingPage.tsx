import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";
import {
  PRODUCT_LIST,
  productPath,
  type ProductPage,
} from "@/lib/products";

/**
 * Flagship U4U marketing surface.
 * Visual posture inspired by the team’s preferred reference (MyHealthPrac):
 * premium clinic feel, sparse 2–3 color system, dual audience, insight tiles,
 * honest disclaimers — not a clone, not a technical dump.
 */

type Props = { product: ProductPage };

const HIGHLIGHTS = [
  {
    title: "Genome-aware options",
    body: "Turn raw genetics into a clearer picture of peptide-relevant biology — structured for a licensed clinician to read.",
  },
  {
    title: "Personal, not generic",
    body: "Built around your file and your context, not a one-size handout. The goal is a decision-ready options set.",
  },
  {
    title: "A loop that learns",
    body: "Pair the first read with follow-up signals over time so the picture can refine as real-world data arrives.",
  },
] as const;

/** Editorial “insight tiles” — qualitative, not invented lab values. */
const INSIGHT_TILES = [
  {
    label: "Genome context",
    title: "What your file can say",
    body: "Variants mapped onto pathways and receptors that matter for peptide and hormone response — plain language first.",
  },
  {
    label: "Options set",
    title: "What to consider next",
    body: "A structured dossier style surface: priorities, cautions, and open questions a clinician can act on.",
  },
  {
    label: "Safety posture",
    title: "Flags before hype",
    body: "Contraindication-minded framing and honest confidence language — no miracle claims on a marketing page.",
  },
  {
    label: "Follow-up",
    title: "How the story continues",
    body: "Room to fuse genetic priors with measured biomarkers so each check-in can tighten the picture.",
  },
  {
    label: "Privacy lane",
    title: "Trust models that fit",
    body: "Cloud product surfaces when you choose them — and a local-first toolkit when you want files to stay put.",
  },
  {
    label: "Research path",
    title: "Built to mature",
    body: "Software ships first. Delivery science and discovery programs sit alongside — labeled as research when they are.",
  },
] as const;

const AUDIENCES = [
  {
    who: "For people",
    title: "Understand your starting point.",
    points: [
      "Bring a genome file you already have (or plan to obtain).",
      "See peptide-relevant context without wading through raw VCF noise.",
      "Leave with something you can take to a licensed clinician — not a self-prescription.",
    ],
  },
  {
    who: "For clinicians & partners",
    title: "A dossier, not a black box.",
    points: [
      "Structured outputs meant to be reviewed, not rubber-stamped by software.",
      "Clear non-goals: not a diagnostic device, not autonomous prescribing.",
      "A path into longitudinal tracking and the broader FMB platform.",
    ],
  },
] as const;

const JOURNEY = [
  {
    step: "01",
    title: "Detect",
    body: "Read the genome and capture real-world signals — files you control, plus optional biomarkers over time.",
  },
  {
    step: "02",
    title: "Design",
    body: "Translate signals into an individualized options set a licensed professional can interpret and decide on.",
  },
  {
    step: "03",
    title: "Deliver",
    body: "Follow response over time in software. Molecular delivery remains a longer-horizon research program.",
  },
] as const;

const QUICK = [
  {
    q: "Is U4U a medical device?",
    a: "No. U4U is research and decision-support software from Florida Man Bioscience. It does not diagnose, treat, cure, or prevent disease.",
  },
  {
    q: "How is this different from PeptOdyssey?",
    a: "U4U is the platform story and product family. PeptOdyssey is the live patient-facing surface for analysis, tracking, and the iOS research path.",
  },
  {
    q: "What about privacy?",
    a: "We offer different trust models: product surfaces when you opt in, and u4u-privacy for local-first work on hardware you control.",
  },
  {
    q: "Can I start today?",
    a: "Yes — open PeptOdyssey to run a genome analysis, or contact the team for partnership and clinical workflow conversations.",
  },
] as const;

export function U4UMarketingPage({ product }: Props) {
  const others = PRODUCT_LIST.filter((p) => p.slug !== product.slug);

  return (
    <CompanyChrome active="products">
      <main className="bg-[#f7f5f0] text-[#0d1117]">
        {/* Hero — premium clinic / sparse palette */}
        <section className="relative overflow-hidden border-b border-[#e6e2d9]">
          <div
            className="pointer-events-none absolute inset-0 opacity-90"
            aria-hidden
            style={{
              background:
                "radial-gradient(90% 70% at 85% 0%, #d9efe4 0%, transparent 55%), radial-gradient(60% 50% at 0% 100%, #efe9dc 0%, transparent 50%)",
            }}
          />
          <div className="relative mx-auto max-w-[1180px] px-6 pb-16 pt-14 md:px-7 md:pb-24 md:pt-20">
            <p
              className="mb-5 text-[11px] font-bold uppercase tracking-[0.18em] text-[#1a6b4a]"
            >
              {product.eyebrow}
            </p>
            <h1
              className="max-w-4xl text-[2.6rem] leading-[1.05] tracking-tight text-[#0d1117] md:text-6xl lg:text-[4.25rem]"
              style={companySerif}
            >
              See beyond the file.
              <span className="mt-2 block text-[#1a6b4a]">
                Unlock genome-aware options.
              </span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-[#3a3f4a] md:text-xl">
              {product.description}
            </p>

            <div className="mt-8 flex flex-wrap gap-2">
              {HIGHLIGHTS.map((h) => (
                <span
                  key={h.title}
                  className="rounded-full border border-[#d5d0c6] bg-white/80 px-3.5 py-1.5 text-xs font-semibold text-[#0f4530] backdrop-blur"
                >
                  {h.title}
                </span>
              ))}
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-3">
              <a
                href={product.ctaPrimary.href}
                className="inline-flex min-h-11 items-center gap-2 rounded-full bg-[#1a6b4a] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#0f4530]"
              >
                {product.ctaPrimary.label}
                <span aria-hidden>→</span>
              </a>
              <Link
                href={product.ctaSecondary.href}
                className="inline-flex min-h-11 items-center gap-2 rounded-full border border-[#cfc9bc] bg-white px-6 py-3 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/45"
              >
                {product.ctaSecondary.label}
              </Link>
            </div>
            <p className="mt-5 max-w-xl text-xs leading-relaxed text-[#6b7280]">
              <span className="font-medium text-[#3a3f4a]">Status: </span>
              {product.statusNote}
            </p>
          </div>
        </section>

        {/* Thesis band */}
        <section className="border-b border-[#e6e2d9] bg-white py-14 md:py-16">
          <div className="mx-auto max-w-[900px] px-6 text-center md:px-7">
            <p
              className="text-3xl leading-snug text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Your biology holds the answers —
              <span className="text-[#1a6b4a]"> we help you read them.</span>
            </p>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-[#3a3f4a]">
              U4U is Florida Man Bioscience’s genome-aware platform for peptide
              medicine: detect carefully, design an options set, and learn from
              what happens next — without turning a website into a lab notebook.
            </p>
          </div>
        </section>

        {/* Insight tiles (MyHealthPrac-like scannable cards, original content) */}
        <section className="border-b border-[#e6e2d9] py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
                  What’s inside
                </p>
                <h2
                  className="mt-2 max-w-xl text-3xl text-[#0d1117] md:text-4xl"
                  style={companySerif}
                >
                  A predictive, personalized surface — for people and
                  practitioners.
                </h2>
              </div>
              <p className="max-w-sm text-sm leading-relaxed text-[#6b7280]">
                Luxury-clinic calm. Fast to load. Two to three colors on purpose
                — so the message, not the chrome, does the work.
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {INSIGHT_TILES.map((tile) => (
                <article
                  key={tile.title}
                  className="group flex min-h-[200px] flex-col justify-between rounded-2xl border border-[#e0dbd1] bg-white p-6 shadow-[0_1px_0_rgba(13,17,23,0.03)] transition hover:border-[#1a6b4a]/30 hover:shadow-[0_18px_40px_-28px_rgba(13,17,23,0.35)]"
                >
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
                      {tile.label}
                    </p>
                    <h3
                      className="mt-3 text-xl text-[#0d1117]"
                      style={companySerif}
                    >
                      {tile.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                      {tile.body}
                    </p>
                  </div>
                  <div
                    className="mt-6 h-px w-12 bg-[#1a6b4a]/35 transition group-hover:w-20"
                    aria-hidden
                  />
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Dual audience */}
        <section className="border-b border-[#e6e2d9] bg-white py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              Designed for you
            </p>
            <h2
              className="mt-2 max-w-2xl text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Built to evolve with how care actually happens.
            </h2>
            <div className="mt-10 grid gap-5 md:grid-cols-2">
              {AUDIENCES.map((block) => (
                <div
                  key={block.who}
                  className="rounded-2xl border border-[#e0dbd1] bg-[#f7f5f0] p-7 md:p-8"
                >
                  <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
                    {block.who}
                  </p>
                  <h3
                    className="mt-3 text-2xl text-[#0d1117]"
                    style={companySerif}
                  >
                    {block.title}
                  </h3>
                  <ul className="mt-5 space-y-3">
                    {block.points.map((p) => (
                      <li
                        key={p}
                        className="flex gap-3 text-sm leading-relaxed text-[#3a3f4a]"
                      >
                        <span
                          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1a6b4a]"
                          aria-hidden
                        />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Journey */}
        <section className="border-b border-[#e6e2d9] py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              The loop
            </p>
            <h2
              className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Detect → Design → Deliver
            </h2>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {JOURNEY.map((j) => (
                <article
                  key={j.step}
                  className="rounded-2xl border border-[#e0dbd1] bg-white p-6"
                >
                  <p className="font-mono text-xs font-medium text-[#6b7280]">
                    {j.step}
                  </p>
                  <h3 className="mt-3 text-2xl text-[#0d1117]" style={companySerif}>
                    {j.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#3a3f4a]">
                    {j.body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Why / highlights expanded */}
        <section className="border-b border-[#e6e2d9] bg-white py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              Why it matters
            </p>
            <h2
              className="mt-2 max-w-2xl text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Marketing that stays honest.
            </h2>
            <div className="mt-10 grid gap-5 md:grid-cols-3">
              {HIGHLIGHTS.map((h) => (
                <article
                  key={h.title}
                  className="rounded-2xl border border-[#e0dbd1] p-6"
                >
                  <div
                    className="mb-4 h-1 w-10 rounded-full bg-[#1a6b4a]"
                    aria-hidden
                  />
                  <h3 className="text-lg text-[#0d1117]" style={companySerif}>
                    {h.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                    {h.body}
                  </p>
                </article>
              ))}
            </div>
            <ul className="mt-10 grid gap-3 sm:grid-cols-3">
              {product.promises.map((item) => (
                <li
                  key={item}
                  className="flex gap-3 rounded-xl border border-[#e0dbd1] bg-[#f7f5f0] px-4 py-3 text-sm text-[#3a3f4a]"
                >
                  <span
                    className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-[#1a6b4a] text-[11px] font-bold text-white"
                    aria-hidden
                  >
                    ✓
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Quick answers */}
        <section className="border-b border-[#e6e2d9] py-16 md:py-20">
          <div className="mx-auto max-w-[900px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              Quick answers
            </p>
            <h2
              className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Straight talk.
            </h2>
            <dl className="mt-10 space-y-4">
              {QUICK.map((item) => (
                <div
                  key={item.q}
                  className="rounded-2xl border border-[#e0dbd1] bg-white px-5 py-5 md:px-6"
                >
                  <dt
                    className="text-lg text-[#0d1117]"
                    style={companySerif}
                  >
                    {item.q}
                  </dt>
                  <dd className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                    {item.a}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* CTA + disclaimer */}
        <section className="border-b border-[#e6e2d9] bg-[#0f4530] py-16 text-[#f7f5f0] md:py-20">
          <div className="mx-auto grid max-w-[1180px] gap-10 px-6 md:grid-cols-[1.2fr_0.8fr] md:px-7">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#a8d5c2]">
                Ready when you are
              </p>
              <h2
                className="mt-3 text-3xl md:text-4xl"
                style={companySerif}
              >
                Take the next step with U4U.
              </h2>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-[#d7ebe1]">
                Start a PeptOdyssey analysis, explore the privacy toolkit, or
                talk with the team about how genome-aware options fit your
                clinic or research workflow.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={product.ctaPrimary.href}
                  className="inline-flex min-h-11 items-center rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#0f4530] hover:bg-[#f7f5f0]"
                >
                  {product.ctaPrimary.label}
                </a>
                <Link
                  href="/products/u4u-privacy"
                  className="inline-flex min-h-11 items-center rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white hover:border-white/60"
                >
                  U4U Privacy
                </Link>
                <a
                  href="mailto:hello@flmanbiosci.net?subject=U4U"
                  className="inline-flex min-h-11 items-center rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white hover:border-white/60"
                >
                  Contact the team
                </a>
              </div>
            </div>
            <aside className="rounded-2xl border border-white/15 bg-white/5 p-6 backdrop-blur">
              <h3 className="text-lg" style={companySerif}>
                Important note
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#d7ebe1]">
                {product.disclaimer}
              </p>
              <p className="mt-4 text-xs leading-relaxed text-[#a8d5c2]">
                Audience: {product.audience}
              </p>
            </aside>
          </div>
        </section>

        {/* Portfolio cross-links */}
        <section className="bg-[#f7f5f0] py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              More from Florida Man Bioscience
            </p>
            <h2
              className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
              style={companySerif}
            >
              Explore the portfolio.
            </h2>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {others.map((p) => (
                <Link
                  key={p.slug}
                  href={productPath(p.slug)}
                  className="group rounded-2xl border border-[#e0dbd1] bg-white p-5 transition hover:border-[#1a6b4a]/35 hover:shadow-[0_12px_30px_-20px_rgba(13,17,23,0.45)]"
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
