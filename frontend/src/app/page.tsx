import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Florida Man Bioscience — Peptide medicine, matched to the genome",
  description:
    "Florida Man Bioscience builds the analytics, trackers, and delivery platform behind precision peptide therapy — genome-aware response prediction, longitudinal biomarkers, and research delivery science.",
  alternates: {
    canonical: "https://flmanbiosci.net/",
  },
  openGraph: {
    title: "Florida Man Bioscience",
    description:
      "Peptide medicine, matched to the genome. Analytics, trackers, and a delivery research platform.",
    url: "https://flmanbiosci.net/",
    siteName: "Florida Man Bioscience",
    type: "website",
  },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

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
    source: "Maps from Predict + Report (PeptidIQ / PeptOdyssey)",
  },
  {
    step: "03",
    title: "Deliver",
    body: "Close the loop over time with Bayesian biomarker tracking — and, on a longer research horizon, molecule-delivery science (MSP nanodisk). Software ships first; delivery stays research-stage.",
    source: "Maps from Track + Deliver in the company platform",
  },
] as const;

const PRODUCTS = [
  {
    name: "PeptOdyssey",
    kicker: "Live product surface",
    blurb:
      "Patient-facing journey: genome analysis on the web, individualized dossier framing, biomarker tracking, and iOS HealthKit research capture.",
    href: "/peptodyssey",
    cta: "Open PeptOdyssey",
    live: true,
  },
  {
    name: "PeptidIQ",
    kicker: "Engine",
    blurb:
      "The genome→response analytics layer: multi-source annotation, peptide mapping, PGx, and evidence-graded priors behind every report.",
    href: "/peptodyssey/analyze",
    cta: "Run an analysis",
    live: true,
  },
  {
    name: "Tracker",
    kicker: "Feedback loop",
    blurb:
      "Longitudinal biomarker tracking that fuses a genetics-informed prior with measured response — turning follow-up into model refinement.",
    href: "/tracking",
    cta: "Open tracker",
    live: true,
  },
  {
    name: "MSP nanodisk",
    kicker: "Delivery · research",
    blurb:
      "Membrane-scaffold-protein nanodisk research for carrying peptide and nucleic-acid payloads. Discovery program — not a marketed therapeutic.",
    href: "#programs",
    cta: "See programs",
    live: false,
  },
] as const;

const SECONDARY = [
  {
    name: "Neuro-creatine & CNS peptides",
    blurb:
      "Early discovery track using the analytics platform to triage candidates and anchor go/no-go decisions in biomarker data.",
  },
  {
    name: "Protein Chemistry",
    blurb:
      "Design and visualization tooling for automated science / DBTL loops — portfolio surface in progress.",
  },
  {
    name: "CytoGate & genomics SaaS",
    blurb:
      "Additional FMB operating surfaces planned; doorways will open here when product copy is ready.",
  },
] as const;

export default function CompanyHomePage() {
  return (
    <div className="-mx-4 -mt-8">
      {/* Full-bleed company surface over the default beige main padding */}
      <div className="bg-[#f5f4f0] text-[#0d1117]">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-[#dbd9d3] bg-white">
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.45]"
            aria-hidden
            style={{
              backgroundImage:
                "radial-gradient(ellipse 80% 60% at 80% 0%, rgba(45,143,97,0.18), transparent 55%), radial-gradient(ellipse 50% 40% at 10% 100%, rgba(30,77,140,0.08), transparent 50%)",
            }}
          />
          <div className="relative mx-auto grid max-w-5xl gap-10 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1a6b4a]">
                Precision peptide therapeutics
              </p>
              <h1
                className="mt-4 text-4xl leading-[1.08] tracking-tight text-[#0d1117] sm:text-5xl lg:text-6xl"
                style={serif}
              >
                Peptide medicine,{" "}
                <em className="not-italic text-[#1a6b4a]">matched to the genome.</em>
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-[#3a3f4a]">
                Florida Man Bioscience builds the analytics, the trackers, and the
                delivery research platform behind precision peptide therapy — so
                each patient can be matched more carefully, and the system learns
                from every measurement.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link
                  href="/peptodyssey"
                  className="inline-flex items-center gap-2 rounded-full bg-[#0d1117] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1a6b4a]"
                >
                  Explore PeptOdyssey
                  <span aria-hidden>→</span>
                </Link>
                <a
                  href="#philosophy"
                  className="inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] bg-white px-6 py-3 text-sm font-semibold text-[#0d1117] transition-colors hover:border-[#1a6b4a]/40 hover:text-[#1a6b4a]"
                >
                  Detect → Design → Deliver
                </a>
              </div>
              <p className="mt-6 max-w-lg text-xs leading-relaxed text-[#6b7280]">
                Decision-support and research tooling with a licensed clinician in
                the loop. Not a medical device; not a guarantee of clinical outcomes.
              </p>
            </div>

            <div className="relative">
              <div className="rounded-2xl border border-[#dbd9d3] bg-gradient-to-br from-[#0d1117] to-[#0f4530] p-6 text-white shadow-[0_24px_60px_-28px_rgba(15,69,48,0.55)] sm:p-8">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#5fd6a0]">
                  Who we are
                </p>
                <p className="mt-3 text-xl leading-snug" style={serif}>
                  A software-first company around one closed loop.
                </p>
                <p className="mt-3 text-sm leading-relaxed text-zinc-300">
                  We treat peptide therapy as a system: read biology, predict and
                  report options clearly, track response over time, and research how
                  to get molecules where they need to go. The analytics layer is in
                  active development; delivery science is research-stage.
                </p>
                <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
                    <dt className="text-[10px] uppercase tracking-wide text-zinc-400">
                      Contact
                    </dt>
                    <dd className="mt-1">
                      <a
                        className="font-medium text-[#5fd6a0] underline-offset-2 hover:underline"
                        href="mailto:hello@flmanbiosci.net"
                      >
                        hello@flmanbiosci.net
                      </a>
                    </dd>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
                    <dt className="text-[10px] uppercase tracking-wide text-zinc-400">
                      Org
                    </dt>
                    <dd className="mt-1">
                      <a
                        className="font-medium text-zinc-100 underline-offset-2 hover:underline"
                        href="https://github.com/Florida-Man-Bioscience"
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        GitHub
                      </a>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </section>

        {/* What we do */}
        <section id="what" className="scroll-mt-20 border-b border-[#dbd9d3] bg-[#f5f4f0]">
          <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1a6b4a]">
              What we do
            </p>
            <h2 className="mt-2 text-3xl text-[#0d1117] sm:text-4xl" style={serif}>
              Stage A: software-first closed loop
            </h2>
            <p className="mt-4 max-w-2xl text-[#3a3f4a]">
              Peptides are still often prescribed one-size-fits-all. We build the
              intelligence layer and measurement loop so response can be informed by
              genetics and refined by data — starting with analytics and tracking,
              not with selling a drug.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                {
                  t: "Analytics",
                  d: "Genome annotation and peptide-response modeling (PeptidIQ / u4u-engine).",
                },
                {
                  t: "Trackers",
                  d: "Bayesian longitudinal biomarkers fused with genetic priors (Tracker).",
                },
                {
                  t: "Delivery research",
                  d: "MSP nanodisk and related payload work — longer horizon, separate regulatory path.",
                },
              ].map((card) => (
                <div
                  key={card.t}
                  className="rounded-2xl border border-[#dbd9d3] bg-white p-5 shadow-sm"
                >
                  <h3 className="text-sm font-semibold text-[#0d1117]">{card.t}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">{card.d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Detect → Design → Deliver */}
        <section
          id="philosophy"
          className="scroll-mt-20 border-b border-[#dbd9d3] bg-white"
        >
          <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1a6b4a]">
              Philosophy
            </p>
            <h2 className="mt-2 text-3xl text-[#0d1117] sm:text-4xl" style={serif}>
              Detect → Design → Deliver
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#3a3f4a]">
              Public three-leg story of how we work. Internally the platform is also
              described as{" "}
              <strong className="font-medium text-[#0d1117]">
                Read → Predict → Report → Track → Deliver
              </strong>
              ; the legs below collapse that loop without inventing new clinical
              claims.
            </p>
            <div className="mt-10 grid gap-5 lg:grid-cols-3">
              {PHILOSOPHY.map((leg) => (
                <article
                  key={leg.title}
                  className="group relative overflow-hidden rounded-2xl border border-[#dbd9d3] bg-[#f5f4f0] p-6 transition-shadow hover:shadow-md"
                >
                  <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#1a6b4a] to-[#2dd4bf]" />
                  <span
                    className="bg-gradient-to-br from-[#1a6b4a] to-[#2d8f61] bg-clip-text text-3xl text-transparent"
                    style={serif}
                  >
                    {leg.step}
                  </span>
                  <h3 className="mt-3 text-xl text-[#0d1117]" style={serif}>
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

        {/* Product doorways */}
        <section
          id="products"
          className="scroll-mt-20 border-b border-[#dbd9d3] bg-[#f5f4f0]"
        >
          <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1a6b4a]">
              Products
            </p>
            <h2 className="mt-2 text-3xl text-[#0d1117] sm:text-4xl" style={serif}>
              Doorways into the platform
            </h2>
            <p className="mt-4 max-w-2xl text-sm text-[#3a3f4a]">
              Live tools sit under PeptOdyssey. Research programs stay descriptive
              until there is a real product surface.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {PRODUCTS.map((p) => (
                <Link
                  key={p.name}
                  href={p.href}
                  className="group flex flex-col rounded-2xl border border-[#dbd9d3] bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#1a6b4a]/35 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1a6b4a]">
                        {p.kicker}
                      </p>
                      <h3 className="mt-1 text-xl text-[#0d1117]" style={serif}>
                        {p.name}
                      </h3>
                    </div>
                    {p.live ? (
                      <span className="shrink-0 rounded-full border border-[#1a6b4a]/25 bg-[#e1f3eb] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#0f4530]">
                        Live
                      </span>
                    ) : (
                      <span className="shrink-0 rounded-full border border-[#dbd9d3] bg-[#edecea] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#6b7280]">
                        Research
                      </span>
                    )}
                  </div>
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-[#3a3f4a]">
                    {p.blurb}
                  </p>
                  <span className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-[#1a6b4a] group-hover:gap-2">
                    {p.cta} <span aria-hidden>→</span>
                  </span>
                </Link>
              ))}
            </div>

            <div id="programs" className="mt-12 scroll-mt-20">
              <h3 className="text-lg text-[#0d1117]" style={serif}>
                Also in the portfolio
              </h3>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {SECONDARY.map((s) => (
                  <div
                    key={s.name}
                    className="rounded-xl border border-dashed border-[#dbd9d3] bg-white/70 p-4"
                  >
                    <p className="text-sm font-semibold text-[#0d1117]">{s.name}</p>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#6b7280]">
                      {s.blurb}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Contact band */}
        <section
          id="contact"
          className="scroll-mt-20 border-b border-[#0f4530] bg-[#0d1117] text-white"
        >
          <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5fd6a0]">
              Contact
            </p>
            <h2 className="mt-2 text-3xl sm:text-4xl" style={serif}>
              Build a peptide program with us.
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-zinc-400">
              Clinicians, collaborators, and investors — we are open on every layer of
              the stack that is ready to share. Prefer email; no overclaim, no cold
              sales funnel.
            </p>
            <a
              href="mailto:hello@flmanbiosci.net"
              className="mt-7 inline-flex items-center gap-2 rounded-full bg-[#2d8f61] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1a6b4a]"
            >
              hello@flmanbiosci.net
              <span aria-hidden>→</span>
            </a>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-[#0b0d12] text-zinc-400">
          <div className="mx-auto grid max-w-5xl gap-8 px-4 py-12 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
            <div className="lg:col-span-1">
              <p className="text-lg text-white" style={serif}>
                Florida Man Bioscience
              </p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-500">
                Peptide-led precision medicine. Built in Florida, opened to the world.
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-300">
                Platform
              </h4>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <Link className="hover:text-white" href="/peptodyssey">
                    PeptOdyssey
                  </Link>
                </li>
                <li>
                  <Link className="hover:text-white" href="/peptodyssey/analyze">
                    Analyze genome
                  </Link>
                </li>
                <li>
                  <Link className="hover:text-white" href="/tracking">
                    Tracker
                  </Link>
                </li>
                <li>
                  <Link className="hover:text-white" href="/regulatory">
                    Regulatory dashboard
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-300">
                Company
              </h4>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <a className="hover:text-white" href="#philosophy">
                    Philosophy
                  </a>
                </li>
                <li>
                  <a className="hover:text-white" href="#products">
                    Products
                  </a>
                </li>
                <li>
                  <a className="hover:text-white" href="#contact">
                    Contact
                  </a>
                </li>
                <li>
                  <a
                    className="hover:text-white"
                    href="https://github.com/Florida-Man-Bioscience"
                    rel="noopener noreferrer"
                    target="_blank"
                  >
                    GitHub
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-300">
                Privacy &amp; product
              </h4>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <Link className="hover:text-white" href="/peptodyssey/privacy">
                    PeptOdyssey privacy
                  </Link>
                </li>
                <li>
                  <Link className="hover:text-white" href="/study">
                    Study
                  </Link>
                </li>
                <li>
                  <Link className="hover:text-white" href="/faq">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10">
            <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
              <span>© {new Date().getFullYear()} Florida Man Bioscience. All rights reserved.</span>
              <span>
                Research &amp; decision-support tools — not medical advice, not a
                device claim.
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
