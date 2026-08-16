import type { Metadata } from "next";
import Link from "next/link";
import { TeamMemberCard } from "@/components/TeamMemberCard";
import { PRODUCT_LIST, productPath } from "@/lib/products";
import { COMPANY_ORIGIN, PRODUCT_ORIGIN } from "@/lib/site";
import { TEAM_HOMEPAGE_PREVIEW } from "@/lib/team";

export const metadata: Metadata = {
  title: "Florida Man Bioscience — Peptide medicine, matched to the genome",
  description:
    "Florida Man Bioscience builds genome-aware peptide decision support — PeptidIQ, the PeptOdyssey dossier, biomarker tracking, and research-stage delivery science.",
  alternates: { canonical: `${COMPANY_ORIGIN}/` },
  openGraph: {
    title: "Florida Man Bioscience",
    description:
      "Peptide medicine, matched to the genome. Decision-support software first; delivery stays research-stage.",
    url: `${COMPANY_ORIGIN}/`,
    siteName: "Florida Man Bioscience",
    type: "website",
  },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

/** Public three-leg story from the company vault (Detect → Design → Deliver). */
const PHILOSOPHY = [
  {
    step: "01",
    title: "Detect",
    body: "A personalized multiomic read: genome files plus measured signals, turned into predictors a licensed clinician can use — not a one-size protocol.",
    source: "Flagship software: PeptidIQ engine + PeptOdyssey dossier",
  },
  {
    step: "02",
    title: "Design",
    body: "Structure-guided design and visualization for peptide and protein work — see the molecule before committing the bench. Software-first; not a wet-lab claim.",
    source: "Stage A design surface: Protein Chemistry / next-gen drug design",
  },
  {
    step: "03",
    title: "Deliver",
    body: "Research on getting payloads where they are needed — MSP / vector nanodisk science. Optionality on a longer horizon, not a marketed therapeutic.",
    source: "Research program only. Institutional IP stays held out until cleared.",
  },
] as const;

const PLATFORM = [
  {
    num: "01 / PeptidIQ",
    title: "Genome → response prediction",
    body: "The engine. Variant annotation, pharmacogenomics, receptor and pathway context — structured so a licensed clinician can read it. Internal platform name: U4U.",
    tag: "Engine",
    href: productPath("u4u"),
  },
  {
    num: "02 / PeptOdyssey",
    title: "The clinician- and patient-facing dossier",
    body: "Decision-support report: safety flags, goal-to-peptide options, citations, and FDA vs investigational labels. The shipping product surface — not a prescription.",
    tag: "Product",
    href: "/peptodyssey",
  },
  {
    num: "03 / Tracker",
    title: "Longitudinal biomarker tracking",
    body: "A Bayesian tracker that fuses the genetic prior with measured biomarkers so the picture can refine over time. Research / decision-support tooling.",
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
                Detect · Design · Deliver
              </p>
              <h1
                className="text-4xl leading-tight text-[#0d1117] md:text-5xl"
                style={serif}
              >
                Peptide medicine,{" "}
                <em className="not-italic text-[#1a6b4a]">matched to the genome.</em>
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-[#3a3f4a]">
                We build the analytics and trackers behind precision peptide
                therapy, with delivery science on a longer research horizon —
                so a licensed clinician can match options more carefully, and
                the system can learn from every measurement.
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
                  alt="Molecular illustration"
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
              Company vision from the working notes: detect predictors, design
              therapies, deliver them where they are needed. Internally the
              software loop is still{" "}
              <strong className="font-medium text-[#0d1117]">
                Read → Predict → Report → Track
              </strong>
              ; delivery is a separate research program.
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
              PeptidIQ reads the genome. PeptOdyssey reports it. The Tracker
              learns from follow-up measurements. Software ships first; delivery
              stays research-stage.
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
                Flagship software first (U4U / PeptOdyssey), then design and
                lab surfaces, then research programs. Neurocreatine and
                nanodisk are early / research — not the current wedge.
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
                The current wedge is clinic decision-support software. Design
                visualization is Stage A. Delivery and CNS discovery are
                research optionality — not marketed products.
              </p>
            </div>

            <div className="grid items-center gap-8 md:grid-cols-2">
              <div className="overflow-hidden rounded-2xl border border-[#dbd9d3] bg-white">
                <picture>
                  <source type="image/webp" srcSet="/assets/img/nanodisk.webp" />
                  <img
                    src="/assets/img/nanodisk.jpg"
                    alt="Molecular illustration"
                    width={1200}
                    height={900}
                    className="w-full object-cover"
                    loading="lazy"
                  />
                </picture>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
                  Shipping wedge
                </p>
                <h3 className="mt-2 text-2xl" style={serif}>
                  PeptOdyssey
                </h3>
                <p className="mt-3 text-[#3a3f4a]">
                  Genomics-guided peptide decision support for longevity,
                  functional, and concierge clinics — a dossier a licensed
                  clinician can read with the patient. Not a prescription, and
                  not a guarantee of response.
                </p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-[#3a3f4a]">
                  <li>VCF / consumer-genome in → structured options out</li>
                  <li>Safety flags and investigational labels called out</li>
                  <li>Clinic-first GTM; prescriber stays in the loop</li>
                </ul>
                <Link
                  href="/peptodyssey"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#1a6b4a] hover:underline"
                >
                  Open PeptOdyssey <span aria-hidden>→</span>
                </Link>
              </div>
            </div>

            <div className="grid items-center gap-8 md:grid-cols-2">
              <div className="order-2 md:order-1">
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#5b3d8c]">
                  Design
                </p>
                <h3 className="mt-2 text-2xl" style={serif}>
                  Next-gen drug design
                </h3>
                <p className="mt-3 text-[#3a3f4a]">
                  Structure-guided visualization and design loops for peptide
                  and protein work — the Design leg. A software surface today,
                  not a wet-lab or clinical product.
                </p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-[#3a3f4a]">
                  <li>See the structure before committing the bench</li>
                  <li>Stage A design / viz — no therapeutic claims</li>
                </ul>
                <Link
                  href={productPath("next-gen-drug-development")}
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#1e4d8c] hover:underline"
                >
                  Design-lab page <span aria-hidden>→</span>
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
                    alt="Structure-guided molecular illustration"
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
              ["PeptidIQ", "Prediction engine"],
              ["7", "Annotation sources"],
              ["CDS", "Clinician in the loop"],
              ["Research", "Delivery program"],
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
              href="mailto:hello@flmanbiosci.net"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#2d8f61]"
            >
              hello@flmanbiosci.net <span aria-hidden>→</span>
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
                  PeptidIQ engine
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
                  href="/peptodyssey"
                  className="hover:text-white"
                >
                  Vector nanodisk
                </Link>
              </li>
              <li>
                <Link
                  href={productPath("next-gen-drug-development")}
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
                <a href="mailto:hello@flmanbiosci.net" className="hover:text-white">
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
