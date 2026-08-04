import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: {
    absolute: "PeptOdyssey — Florida Man Bioscience",
  },
  description:
    "PeptOdyssey is Florida Man Bioscience’s precision peptide genomics surface: genome analysis, individualized reporting, biomarker tracking, and iOS HealthKit research capture.",
  alternates: {
    canonical: "https://flmanbiosci.net/peptodyssey",
  },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

const LINKS = [
  {
    href: "/peptodyssey/analyze",
    title: "Analyze",
    desc: "Upload a genome file (VCF, 23andMe-style txt, or CSV) for peptide-oriented variant analysis.",
  },
  {
    href: "/jobs",
    title: "History",
    desc: "Past analysis jobs and result dossiers.",
  },
  {
    href: "/tracking",
    title: "Tracker",
    desc: "Longitudinal biomarkers with Bayesian posteriors and genetics-informed priors.",
  },
  {
    href: "/regulatory",
    title: "Regulatory",
    desc: "Live peptide regulatory context dashboard (research tooling).",
  },
  {
    href: "/study",
    title: "Study",
    desc: "Observational study surface and enrollment context.",
  },
  {
    href: "/peptodyssey/privacy",
    title: "Privacy",
    desc: "iOS / HealthKit privacy policy — App Store and TestFlight URL.",
  },
  {
    href: "/faq",
    title: "FAQ",
    desc: "Science, projections, and model accountability questions.",
  },
  {
    href: "/tracking/model",
    title: "Model docs",
    desc: "Formalization of the Bayesian peptide-response model used in tracking.",
  },
] as const;

export default function PeptodysseyHubPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-10 pb-16">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          Product · Florida Man Bioscience
        </p>
        <h1 className="mt-3 text-4xl leading-tight text-[#0d1117]" style={serif}>
          PeptOdyssey
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-[#3a3f4a]">
          The patient-facing product surface for precision peptide genomics:
          genome → annotated options, a clear dossier framing, longitudinal
          biomarker tracking, and consented HealthKit capture on iOS.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-[#6b7280]">
          Built for research and clinician-in-the-loop decision support. It does
          not diagnose, treat, cure, or prevent disease, and it is not a medical
          device.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link
          href="/peptodyssey/analyze"
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#1a6b4a] to-[#2d8f61] px-6 py-3 text-sm font-semibold text-white shadow-md shadow-[#1a6b4a]/20 transition-transform hover:-translate-y-0.5"
        >
          Start analysis
          <span aria-hidden>→</span>
        </Link>
        <Link
          href="/peptodyssey/privacy"
          className="inline-flex items-center gap-2 rounded-xl border border-[#dbd9d3] bg-white px-6 py-3 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
        >
          Privacy policy
        </Link>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-[#6b7280] hover:text-[#1a6b4a]"
        >
          ← Florida Man Bioscience
        </Link>
      </div>

      <section className="grid gap-3 sm:grid-cols-2">
        {LINKS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-xl border border-[#dbd9d3] bg-white p-5 transition-colors hover:border-[#1a6b4a]/40 hover:bg-[#e1f3eb]/30"
          >
            <h2 className="text-base font-semibold text-[#0d1117]">{item.title}</h2>
            <p className="mt-1.5 text-sm leading-relaxed text-[#3a3f4a]">
              {item.desc}
            </p>
          </Link>
        ))}
      </section>

      <aside className="rounded-lg border border-[#dbd9d3] border-l-4 border-l-[#1a6b4a] bg-white px-4 py-3 text-sm text-[#3a3f4a]">
        <strong className="text-[#0d1117]">Engine under the hood.</strong> Analysis
        runs on the open PeptidIQ / u4u-engine pipeline (annotation, PGx, peptide
        mapping, Bayesian tracking). Company story and philosophy live on the{" "}
        <Link href="/" className="font-medium text-[#1a6b4a] underline">
          Florida Man Bioscience homepage
        </Link>
        .
      </aside>
    </div>
  );
}
