import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "PeptOdyssey",
  description:
    "PeptOdyssey — precision peptide genomics: genome analysis, longitudinal biomarker tracking, regulatory context, and the iOS research app privacy policy.",
  alternates: { canonical: "https://peptodyssey.flmanbiosci.net/peptodyssey" },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

const LINKS = [
  {
    href: "/peptodyssey/analyze",
    kicker: "Core tool",
    title: "Genome analysis",
    body: "Upload a VCF, 23andMe, or CSV file. Annotate variants and map them onto peptide-relevant biology.",
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
    kicker: "Context",
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
    body: "What the engine analyses, how evidence grades work, and how to read projections.",
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
    body: "Company home — platform story, programs, team, and contact.",
  },
] as const;

export default function PeptodysseyHubPage() {
  return (
    <div className="space-y-10 pb-10">
      <div className="space-y-3">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          Product hub
        </p>
        <h1 className="text-4xl leading-tight text-[#0d1117]" style={serif}>
          PeptOdyssey
        </h1>
        <p className="max-w-2xl text-[#3a3f4a]">
          Precision peptide genomics from Florida Man Bioscience. Start a genome
          analysis, follow biomarkers over time, or open the iOS research-app
          privacy policy used for TestFlight.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="/peptodyssey/analyze"
            className="inline-flex items-center rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
          >
            New analysis
          </Link>
          <Link
            href="/privacy"
            className="inline-flex items-center rounded-full border border-[#dbd9d3] bg-white px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
          >
            Privacy policy
          </Link>
        </div>
      </div>

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
