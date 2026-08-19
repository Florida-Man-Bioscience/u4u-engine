import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "PeptOdyssey",
  description:
    "PeptOdyssey — Florida Man Bioscience’s peptide platform: genome analysis, clinician-readable dossier, longitudinal tracking, and iOS research capture.",
  alternates: { canonical: "https://peptodyssey.flmanbiosci.net/peptodyssey" },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

const LOOP = [
  {
    step: "01",
    title: "Genome",
    body: "Upload a VCF, 23andMe, or CSV. The engine annotates variants onto peptide-relevant biology.",
    href: "/peptodyssey/analyze",
  },
  {
    step: "02",
    title: "Dossier",
    body: "A clinician-readable options set: safety flags, citations, and FDA vs investigational labels.",
    href: "/jobs",
  },
  {
    step: "03",
    title: "Tracking",
    body: "Bayesian updates that fuse the genetic prior with measured biomarkers over time.",
    href: "/tracking",
  },
] as const;

const LINKS = [
  {
    href: "/peptodyssey/analyze",
    kicker: "Start here",
    title: "Demo analysis",
    body: "Research decision-support only — not diagnosis or treatment. Upload a file and see the loop.",
  },
  {
    href: "/tracking",
    kicker: "Longitudinal",
    title: "Biomarker tracking",
    body: "Bayesian posterior updates that fuse genetic priors with measured biomarkers over time.",
  },
  {
    href: "/jobs",
    kicker: "History",
    title: "Past analyses",
    body: "Browse completed and in-flight analysis jobs for this session or account.",
  },
  {
    href: "/regulatory",
    kicker: "Credibility",
    title: "Peptide regulatory dashboard",
    body: "Curated peptide FDA status merged with live ClinicalTrials.gov, openFDA, and Federal Register signals.",
  },
  {
    href: "/study",
    kicker: "Research",
    title: "Pipeline validation study",
    body: "Enrollment and development surface for the validation study pathway.",
  },
  {
    href: "/faq",
    kicker: "Help",
    title: "FAQ",
    body: "What the engine analyses, how evidence grades A–D work, and how ACMG human sign-off is framed.",
  },
  {
    href: "/peptodyssey/privacy",
    kicker: "iOS / TestFlight",
    title: "Privacy policy",
    body: "HealthKit data types, purpose, retention, deletion, and contact — required App Store / TestFlight disclosure URL.",
  },
  {
    href: "/",
    kicker: "Company",
    title: "Florida Man Bioscience",
    body: "Company home — Detect → Design → Deliver, programs, team, and contact.",
  },
] as const;

export default function PeptodysseyHubPage() {
  return (
    <div className="space-y-12 pb-10">
      <div className="space-y-3">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          Product
        </p>
        <h1 className="text-4xl leading-tight text-[#0d1117]" style={serif}>
          PeptOdyssey
        </h1>
        <p className="max-w-2xl text-[#3a3f4a]">
          Florida Man Bioscience’s peptide platform for licensed clinicians:
          genome analysis, a readable dossier, and biomarker follow-up. Research
          decision-support — not a prescription, not a diagnosis.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="/peptodyssey/analyze"
            className="inline-flex items-center rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
          >
            Start a demo analysis
          </Link>
          <a
            href="mailto:hello@flmanbiosci.net?subject=PeptOdyssey%20clinic"
            className="inline-flex items-center rounded-full border border-[#dbd9d3] bg-white px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
          >
            Partner / contact
          </a>
        </div>
      </div>

      <section className="rounded-2xl border border-[#dbd9d3] bg-[#f5f4f0] p-6 md:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          The loop
        </p>
        <h2 className="mt-2 text-2xl text-[#0d1117]" style={serif}>
          Genome → dossier → tracking
        </h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {LOOP.map((item) => (
            <Link
              key={item.step}
              href={item.href}
              className="rounded-xl border border-[#dbd9d3] bg-white p-5 hover:border-[#1a6b4a]/40"
            >
              <p className="font-mono text-xs text-[#6b7280]">{item.step}</p>
              <h3 className="mt-2 text-xl" style={serif}>
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                {item.body}
              </p>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-[#dbd9d3] bg-white p-6 md:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          Trust
        </p>
        <h2 className="mt-2 text-2xl text-[#0d1117]" style={serif}>
          Independent peptide verification matters.
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#3a3f4a]">
          Without a third-party check, you may not be injecting what the label
          says. Independent analysis has shown only a fraction of tested samples
          match the label. This platform does not replace identity testing of
          the vial.
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        {LINKS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="group flex flex-col rounded-xl border border-[#dbd9d3] bg-white p-5 transition hover:border-[#1a6b4a]/40 hover:shadow-sm"
          >
            <span className="text-xs font-bold uppercase tracking-[0.1em] text-[#1a6b4a]">
              {item.kicker}
            </span>
            <span
              className="mt-2 text-xl text-[#0d1117] group-hover:text-[#0f4530]"
              style={serif}
            >
              {item.title}
            </span>
            <span className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
              {item.body}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
