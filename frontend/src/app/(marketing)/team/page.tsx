import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";
import { TeamMemberCard } from "@/components/TeamMemberCard";
import {
  ADVISORS,
  CONTRIBUTORS,
  FOUNDERS,
  NUCLEATE_ACTIVATOR_MEMBERS,
} from "@/lib/team";
import { COMPANY_ORIGIN } from "@/lib/site";

export const metadata: Metadata = {
  title: "Team — Florida Man Bioscience",
  description:
    "Founders, Nucleate Activator contributors, and advisors behind Florida Man Bioscience and PeptOdyssey.",
  alternates: { canonical: `${COMPANY_ORIGIN}/team` },
  openGraph: {
    title: "Team — Florida Man Bioscience",
    description:
      "The full team: founders and 2026 Nucleate Activator contributors building precision peptide medicine.",
    url: `${COMPANY_ORIGIN}/team`,
    siteName: "Florida Man Bioscience",
    type: "website",
  },
};

function Section({
  eyebrow,
  title,
  intro,
  children,
}: {
  eyebrow: string;
  title: string;
  intro: string;
  children: ReactNode;
}) {
  return (
    <section className="scroll-mt-24 border-t border-[#edecea] py-14 md:py-16">
      <div className="mx-auto max-w-[1180px] px-6 md:px-7">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
          {eyebrow}
        </p>
        <h2
          className="mt-2 text-3xl text-[#0d1117] md:text-4xl"
          style={companySerif}
        >
          {title}
        </h2>
        <p className="mt-3 max-w-2xl text-[#3a3f4a]">{intro}</p>
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {children}
        </div>
      </div>
    </section>
  );
}

export default function TeamPage() {
  const activatorCount = NUCLEATE_ACTIVATOR_MEMBERS.length;

  return (
    <CompanyChrome active="team">
      <main>
        <section className="border-b border-[#edecea] bg-[#f5f4f0]">
          <div className="mx-auto max-w-[1180px] px-6 py-16 md:px-7 md:py-20">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
              Company
            </p>
            <h1
              className="max-w-3xl text-4xl leading-tight text-[#0d1117] md:text-5xl"
              style={companySerif}
            >
              The people behind Florida Man Bioscience.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[#3a3f4a]">
              Founders, operators, and the full {activatorCount}-person cohort
              from our{" "}
              <strong className="font-semibold text-[#0d1117]">
                2026 Nucleate Activator
              </strong>{" "}
              challenge — scientists and builders who refuse to choose between
              rigor and speed.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#founders"
                className="inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
              >
                Founding team
              </a>
              <a
                href="#activator"
                className="inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] bg-white px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
              >
                Nucleate Activator contributors
              </a>
            </div>
          </div>
        </section>

        <div id="founders">
          <Section
            eyebrow="Founding team"
            title="Six founders."
            intro="Public roles as shown on the company site. Formal titles and equity structure live in internal governance — not restated here."
          >
            {FOUNDERS.map((m) => (
              <TeamMemberCard key={m.id} member={m} />
            ))}
          </Section>
        </div>

        <div id="activator" className="bg-[#f5f4f0]">
          <Section
            eyebrow="2026 Nucleate Activator"
            title="Contributors who built with us."
            intro="Everyone who joined the Activator cohort and extended build — clinical, safety, oncology genetics, metabolism, engineering, GTM, and ops. Includes Rocky Truong, Kayla Schwartz, Min Young Park, Sasank Desaraju, and the full contributor bench."
          >
            {CONTRIBUTORS.map((m) => (
              <TeamMemberCard key={m.id} member={m} />
            ))}
          </Section>
        </div>

        <div id="advisors">
          <Section
            eyebrow="Advisors"
            title="Strategic guidance."
            intro="External advisors supporting commercialization and partnerships."
          >
            {ADVISORS.map((m) => (
              <TeamMemberCard key={m.id} member={m} />
            ))}
          </Section>
        </div>

        <section className="border-t border-[#edecea] bg-[#0d1117] py-16 text-white md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#2d8f61]">
              Work with us
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={companySerif}>
              Clinics, collaborators, builders.
            </h2>
            <p className="mt-3 max-w-xl text-zinc-400">
              Whether you are a clinician, scientist, or operator — we are open
              to collaboration across the Detect → Design → Deliver stack.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="mailto:hello@flmanbiosci.net"
                className="inline-flex items-center gap-2 rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#2d8f61]"
              >
                hello@flmanbiosci.net <span aria-hidden>→</span>
              </a>
              <Link
                href="/peptodyssey"
                className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-2.5 text-sm font-semibold text-white hover:border-white/40"
              >
                Explore PeptOdyssey
              </Link>
            </div>
          </div>
        </section>
      </main>
    </CompanyChrome>
  );
}
