import type { Metadata } from "next";
import Link from "next/link";
import { TeamMemberCard } from "@/components/TeamMemberCard";
import { PRODUCT_LIST, productPath } from "@/lib/products";
import { COMPANY_ORIGIN, PRODUCT_ORIGIN } from "@/lib/site";
import { TEAM_HOMEPAGE_PREVIEW } from "@/lib/team";

export const metadata: Metadata = {
  title: "Florida Man Bioscience — Peptide medicine, matched to the genome",
  description:
    "Florida Man Bioscience builds the analytics, trackers, and delivery platform behind precision peptide therapy — genome-aware response prediction, longitudinal biomarkers, and research delivery science.",
  alternates: { canonical: `${COMPANY_ORIGIN}/` },
  openGraph: {
    title: "Florida Man Bioscience",
    description:
      "Peptide medicine, matched to the genome. Analytics, trackers, and a delivery research platform.",
    url: `${COMPANY_ORIGIN}/`,
    siteName: "Florida Man Bioscience",
    type: "website",
  },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

/** Public three-leg story (Detect→Design→Deliver). Maps the internal
 *  Read→Predict→Report→Track→Deliver loop without inventing clinical claims. */
const PHILOSOPHY = [
  {
    step: "01",
    title: "Detect",
    body: "Read the genome and capture real-world signals — raw VCF or consumer genetics files, plus longitudinal biomarkers from labs and consented HealthKit capture.",
    source: "Maps from Read + measure in the U4U loop",
  },
  {
    step: "02",
    title: "Design",
    body: "Turn signals into a clear, individualized options set: variant annotation, pharmacogenomics, receptor and pathway context, and a dossier a licensed clinician can read and decide on.",
    source: "Maps from Predict + Report (u4u-engine / PeptOdyssey)",
  },
  {
    step: "03",
    title: "Deliver",
    body: "Close the loop over time with Bayesian biomarker tracking — and, on a longer research horizon, molecule-delivery science (MSP nanodisk). Software ships first; delivery stays research-stage.",
    source: "Maps from Track + Deliver in the company platform",
  },
] as const;

const PLATFORM = [
  {
    num: "01 / U4U",
    title: "Genome-aware platform",
    body: "The flagship story: turn genetic context into a clearer peptide options set for people and licensed clinicians — premium product marketing, honest non-goals.",
    tag: "Flagship",
    href: productPath("u4u"),
  },
  {
    num: "02 / PeptOdyssey",
    title: "The patient-facing product",
    body: "Dossier, longitudinal tracking, and the iOS HealthKit capture loop — translating engine findings into individualized peptide options, safety flags, and measurable follow-up.",
    tag: "Product",
    href: "/peptodyssey",
  },
  {
    num: "03 / Tracker",
    title: "Longitudinal biomarker tracking",
    body: "A Bayesian tracker that fuses the patient's genetic prior with measured biomarkers to refine the prediction over time — turning each appointment into training data.",
    tag: "Feedback loop",
    href: PRODUCT_ORIGIN + "/tracking",
  },
] as const;

/** Public product / program marketing pages on apex (also mirrored on portfolio hosts). */
const PORTFOLIO = PRODUCT_LIST.map((p) => ({
  name: p.name,
  body: p.cardBody,
  href: productPath(p.slug),
  tag: p.tag,
}));

export default function CompanyHomePage() {
  return (
    <div className="bg-white text-[#0d1117]">
      {/* Company nav */}
      <header className="sticky top-0 z-50 border-b border-[#edecea] bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1180px] items-center justify-between px-6 md:px-7">
          <Link href="/" className="flex items-center gap-2.5">
            <span
              className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-[#1a6b4a] to-[#0f4530] text-sm text-white"
              style={serif}
              aria-hidden
            >
              F
            </span>
            <span className="text-lg tracking-tight text-[#0d1117]" style={serif}>
              Florida Man Bioscience
            </span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm font-medium text-[#3a3f4a] sm:flex">
            <a href="#philosophy" className="hover:text-[#1a6b4a]">
              Philosophy
            </a>
            <a href="#platform" className="hover:text-[#1a6b4a]">
              Platform
            </a>
            <a href="#products" className="hover:text-[#1a6b4a]">
              Programs
            </a>
            <Link href="/team" className="hover:text-[#1a6b4a]">
              Team
            </Link>
            <Link
              href={"/peptodyssey"}
              className="rounded-full bg-[#1a6b4a] px-4 py-2 text-white hover:bg-[#0f4530]"
            >
              PeptOdyssey
            </Link>
          </nav>
          <Link
            href={"/peptodyssey"}
            className="rounded-full bg-[#1a6b4a] px-3 py-1.5 text-sm font-medium text-white sm:hidden"
          >
            Product
          </Link>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="border-b border-[#edecea]">
          <div className="mx-auto grid max-w-[1180px] gap-10 px-6 py-16 md:grid-cols-2 md:items-center md:px-7 md:py-24">
            <div>
              <p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
                Precision peptide therapeutics
              </p>
              <h1
                className="text-4xl leading-tight text-[#0d1117] md:text-5xl"
                style={serif}
              >
                Peptide medicine,{" "}
                <em className="not-italic text-[#1a6b4a]">matched to the genome.</em>
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-[#3a3f4a]">
                We build the analytics, the trackers, and the delivery research
                platform behind precision peptide therapy — so each patient can
                be matched more carefully, and the system learns from every
                measurement.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href={"/peptodyssey"}
                  className="inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
                >
                  Explore PeptOdyssey <span aria-hidden>→</span>
                </Link>
                <a
                  href="#philosophy"
                  className="inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] bg-white px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
                >
                  Detect → Design → Deliver
                </a>
                <a
                  href="#contact"
                  className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold text-[#1a6b4a] hover:underline"
                >
                  Partner with us
                </a>
              </div>
              <p className="mt-5 max-w-lg text-xs leading-relaxed text-[#6b7280]">
                Decision-support and research tooling with a licensed clinician in
                the loop. Not a medical device; not a guarantee of clinical outcomes.
              </p>
            </div>
            <div className="overflow-hidden rounded-2xl border border-[#dbd9d3] bg-[#f5f4f0]">
              <picture>
                <source
                  type="image/webp"
                  srcSet="/assets/img/neurocreatine.webp"
                />
                <img
                  src="/assets/img/neurocreatine.jpg"
                  alt="Molecular illustration of a brain peptide concept"
                  width={1000}
                  height={750}
                  className="h-full w-full object-cover"
                  fetchPriority="high"
                />
              </picture>
            </div>
          </div>
        </section>

        {/* Detect → Design → Deliver */}
        <section
          id="philosophy"
          className="scroll-mt-24 border-b border-[#edecea] bg-[#f5f4f0] py-16 md:py-20"
        >
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
              Philosophy
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={serif}>
              Detect → Design → Deliver
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#3a3f4a]">
              Public three-leg story of how we work. Internally the platform is
              also described as{" "}
              <strong className="font-medium text-[#0d1117]">
                Read → Predict → Report → Track → Deliver
              </strong>
              ; the legs below collapse that loop without inventing new clinical
              claims.
            </p>
            <div className="mt-10 grid gap-5 md:grid-cols-3">
              {PHILOSOPHY.map((leg) => (
                <article
                  key={leg.title}
                  className="relative overflow-hidden rounded-xl border border-[#dbd9d3] bg-white p-6"
                >
                  <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#1a6b4a] to-[#2dd4bf]" />
                  <span
                    className="bg-gradient-to-br from-[#1a6b4a] to-[#2d8f61] bg-clip-text text-3xl text-transparent"
                    style={serif}
                  >
                    {leg.step}
                  </span>
                  <h3 className="mt-3 text-xl" style={serif}>
                    {leg.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#3a3f4a]">
                    {leg.body}
                  </p>
                  <p className="mt-4 text-[11px] uppercase tracking-wide text-[#6b7280]">
                    {leg.source}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Platform */}
        <section id="platform" className="scroll-mt-24 py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
              Platform
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={serif}>
              Three layers, one feedback loop.
            </h2>
            <p className="mt-3 max-w-2xl text-[#3a3f4a]">
              Our platform reads the genome, designs the options set, and learns
              from the response — software first; delivery research on a longer
              horizon.
            </p>
            <div className="mt-10 grid gap-5 md:grid-cols-3">
              {PLATFORM.map((card) => (
                <Link
                  key={card.num}
                  href={card.href}
                  className="flex h-full flex-col rounded-xl border border-[#dbd9d3] bg-[#f5f4f0] p-6 transition hover:border-[#1a6b4a]/35"
                >
                  <p className="font-mono text-xs font-medium text-[#6b7280]">
                    {card.num}
                  </p>
                  <h3 className="mt-3 text-xl" style={serif}>
                    {card.title}
                  </h3>
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-[#3a3f4a]">
                    {card.body}
                  </p>
                  <span className="mt-5 inline-flex w-fit rounded-full bg-[#e1f3eb] px-2.5 py-1 text-xs font-semibold text-[#0f4530]">
                    {card.tag}
                  </span>
                </Link>
              ))}
            </div>
            <div className="mt-8">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#6b7280]">
                Product pages
              </p>
              <p className="mt-2 max-w-2xl text-sm text-[#3a3f4a]">
                Flagship U4U plus portfolio programs — CytoGate, vector
                nanodisk, Neurocreatine, U4U Privacy, and next-gen drug
                development.
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {PORTFOLIO.map((card) => (
                  <Link
                    key={card.name}
                    href={card.href}
                    className="flex flex-col rounded-xl border border-dashed border-[#dbd9d3] bg-white p-5 transition hover:border-[#1a6b4a]/40"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="text-lg text-[#0d1117]" style={serif}>
                        {card.name}
                      </h3>
                      <span className="rounded-full bg-[#f5f4f0] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#6b7280]">
                        {card.tag}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                      {card.body}
                    </p>
                    <span className="mt-3 text-sm font-medium text-[#1a6b4a]">
                      Open product page →
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Programs */}
        <section
          id="products"
          className="scroll-mt-24 border-y border-[#edecea] bg-[#f5f4f0] py-16 md:py-20"
        >
          <div className="mx-auto max-w-[1180px] space-y-14 px-6 md:px-7">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
                Programs
              </p>
              <h2 className="mt-2 text-3xl md:text-4xl" style={serif}>
                What we are building.
              </h2>
              <p className="mt-3 max-w-2xl text-[#3a3f4a]">
                From the analytics layer down to molecular delivery, our pipeline
                is built around peptides — drugs that can be precise, but only if
                you treat them as a system.
              </p>
            </div>

            <div className="grid items-center gap-8 md:grid-cols-2">
              <div className="overflow-hidden rounded-2xl border border-[#dbd9d3] bg-white">
                <picture>
                  <source type="image/webp" srcSet="/assets/img/nanodisk.webp" />
                  <img
                    src="/assets/img/nanodisk.jpg"
                    alt="Nanodisk delivery vehicle illustration"
                    width={1200}
                    height={900}
                    className="w-full object-cover"
                    loading="lazy"
                  />
                </picture>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#92550a]">
                  Delivery
                </p>
                <h3 className="mt-2 text-2xl" style={serif}>
                  Vector nanodisk delivery
                </h3>
                <p className="mt-3 text-[#3a3f4a]">
                  A research-stage delivery program exploring how peptide and
                  nucleic-acid payloads can be carried more carefully — the
                  long-horizon Deliver leg of the platform.
                </p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-[#3a3f4a]">
                  <li>Molecule delivery as a system, not a side project</li>
                  <li>Research-first positioning — not a marketed therapeutic</li>
                  <li>Open to thoughtful scientific partnership</li>
                </ul>
                <Link
                  href={productPath("vector-nanodisk")}
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#92550a] hover:underline"
                >
                  Vector nanodisk product page <span aria-hidden>→</span>
                </Link>
              </div>
            </div>

            <div className="grid items-center gap-8 md:grid-cols-2">
              <div className="order-2 md:order-1">
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1e4d8c]">
                  Discovery
                </p>
                <h3 className="mt-2 text-2xl" style={serif}>
                  Neurocreatine
                </h3>
                <p className="mt-3 text-[#3a3f4a]">
                  An early-stage discovery track exploring peptides aimed at the
                  central nervous system — with go/no-go decisions anchored in
                  measurable signals, not hype.
                </p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-[#3a3f4a]">
                  <li>Discovery with discipline</li>
                  <li>Measurement-minded triage</li>
                </ul>
                <Link
                  href={productPath("neurocreatine")}
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#1e4d8c] hover:underline"
                >
                  Neurocreatine product page <span aria-hidden>→</span>
                </Link>
              </div>
              <div className="order-1 overflow-hidden rounded-2xl border border-[#dbd9d3] bg-white md:order-2">
                <picture>
                  <source
                    type="image/webp"
                    srcSet="/assets/img/neurocreatine.webp"
                  />
                  <img
                    src="/assets/img/neurocreatine.jpg"
                    alt="Neuro-creatine concept"
                    width={1000}
                    height={750}
                    className="w-full object-cover"
                    loading="lazy"
                  />
                </picture>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-12">
          <div className="mx-auto grid max-w-[1180px] grid-cols-2 gap-4 px-6 md:grid-cols-4 md:px-7">
            {[
              ["50+", "Biomarkers tracked"],
              ["7", "Annotation sources"],
              ["Bayesian", "Posterior updates"],
              ["Open", "Source engine"],
            ].map(([n, l]) => (
              <div
                key={l}
                className="rounded-xl border border-[#dbd9d3] bg-white px-4 py-5 text-center"
              >
                <div className="text-2xl text-[#1a6b4a]" style={serif}>
                  {n}
                </div>
                <div className="mt-1 text-xs font-medium uppercase tracking-wide text-[#6b7280]">
                  {l}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Team preview → full roster on /team */}
        <section
          id="team"
          className="scroll-mt-24 border-t border-[#edecea] bg-[#f5f4f0] py-16 md:py-20"
        >
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
              Team
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={serif}>
              The people behind the science.
            </h2>
            <p className="mt-3 max-w-2xl text-[#3a3f4a]">
              Founders plus the full 2026 Nucleate Activator cohort — Rocky,
              Kayla, Min, Sasank, and every contributor who built with us.
            </p>
            <div className="mt-10 grid grid-cols-2 gap-5 md:grid-cols-3">
              {TEAM_HOMEPAGE_PREVIEW.map((m) => (
                <TeamMemberCard key={m.id} member={m} compact />
              ))}
            </div>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                href="/team"
                className="inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
              >
                Full team &amp; Activator contributors{" "}
                <span aria-hidden>→</span>
              </Link>
              <p className="text-xs text-[#6b7280]">
                Public marketing roles only. Formal titles and equity are
                internal governance — not restated here.
              </p>
            </div>
          </div>
        </section>

        {/* Contact */}
        <section
          id="contact"
          className="scroll-mt-24 bg-[#0d1117] py-16 text-white md:py-20"
        >
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#2d8f61]">
              Get in touch
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={serif}>
              Build a peptide program with us.
            </h2>
            <p className="mt-3 max-w-xl text-zinc-400">
              Whether you are a clinician, investor, or scientist — we are open
              to collaboration on every layer of the stack.
            </p>
            <a
              href="mailto:noahtjones@gmail.com"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#2d8f61]"
            >
              noahtjones@gmail.com <span aria-hidden>→</span>
            </a>
          </div>
        </section>
      </main>

      <footer className="border-t border-[#1a1f2a] bg-[#08090d] py-12 text-sm text-zinc-400">
        <div className="mx-auto grid max-w-[1180px] gap-8 px-6 md:grid-cols-4 md:px-7">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 text-white">
              <span
                className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-[#1a6b4a] to-[#0f4530] text-xs"
                style={serif}
              >
                F
              </span>
              <span style={serif}>Florida Man Bioscience</span>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-zinc-500">
              Peptide-led precision medicine. Built in Florida, opened to the
              world.
            </p>
          </div>
          <div>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-300">
              Platform
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#philosophy" className="hover:text-white">
                  Detect → Design → Deliver
                </a>
              </li>
              <li>
                <Link href={productPath("u4u")} className="hover:text-white">
                  U4U
                </Link>
              </li>
              <li>
                <a href="#platform" className="hover:text-white">
                  PeptOdyssey engine
                </a>
              </li>
              <li>
                <Link href={productPath("cytogate")} className="hover:text-white">
                  CytoGate
                </Link>
              </li>
              <li>
                <Link
                  href={productPath("u4u-privacy")}
                  className="hover:text-white"
                >
                  U4U Privacy
                </Link>
              </li>
              <li>
                <Link
                  href={productPath("vector-nanodisk")}
                  className="hover:text-white"
                >
                  Vector nanodisk
                </Link>
              </li>
              <li>
                <Link
                  href={productPath("neurocreatine")}
                  className="hover:text-white"
                >
                  Neurocreatine
                </Link>
              </li>
              <li>
                <Link
                  href={productPath("next-gen-drug-development")}
                  className="hover:text-white"
                >
                  Next-gen drug development
                </Link>
              </li>
              <li>
                <Link href={"/peptodyssey"} className="hover:text-white">
                  PeptOdyssey
                </Link>
              </li>
              <li>
                <Link href={"/tracking"} className="hover:text-white">
                  Biomarker tracker
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-300">
              Product
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href={"/peptodyssey/analyze"} className="hover:text-white">
                  Genome analysis
                </Link>
              </li>
              <li>
                <Link href={"/peptodyssey/privacy"} className="hover:text-white">
                  iOS privacy policy
                </Link>
              </li>
              <li>
                <Link href={"/study"} className="hover:text-white">
                  Validation study
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-300">
              Company
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/team" className="hover:text-white">
                  Team
                </Link>
              </li>
              <li>
                <a href="mailto:noahtjones@gmail.com" className="hover:text-white">
                  Contact
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Florida-Man-Bioscience"
                  rel="noopener noreferrer"
                  className="hover:text-white"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mx-auto mt-10 flex max-w-[1180px] flex-wrap justify-between gap-2 border-t border-white/5 px-6 pt-6 text-xs text-zinc-600 md:px-7">
          <span>© {new Date().getFullYear()} Florida Man Bioscience. All rights reserved.</span>
          <span>Built in Florida.</span>
        </div>
      </footer>
    </div>
  );
}
