import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Validation Study — Development Hub — PeptOdyssey",
  description:
    "Development hub for the human-subjects study validating the u4u-engine genomic pipeline: three-tier IRB partition, regulatory pathway, guardrails, and live status.",
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

function Pip({ tone }: { tone: "ok" | "warn" | "danger" | "info" }) {
  const c = {
    ok: "bg-[#15803d]",
    warn: "bg-[#d97706]",
    danger: "bg-[#b91c1c]",
    info: "bg-[#2563eb]",
  }[tone];
  return <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${c}`} />;
}

function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-[#dbd9d3] border-l-[3px] border-l-[#1a6b4a] bg-[#edecea] px-4 py-3.5 text-[0.92rem] text-[#3a3f4a]">
      {children}
    </div>
  );
}

export default function StudyDevPage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#1a6b4a]">
          Human-subjects research · development hub
        </p>
        <h1 className="text-4xl leading-tight text-[#0d1117]" style={serif}>
          Validating the performance of the u4u-engine genomic pipeline
        </h1>
        <p className="max-w-[60ch] text-lg text-[#3a3f4a]">
          An observational diagnostic- and predictive-accuracy study: does the pipeline compute the
          right answer when the right answer is already known? This hub consolidates the study&apos;s
          structure, regulatory pathway, design guardrails, and live status into one place so the
          protocol can be developed without re-deriving decisions that are already settled.
        </p>
        <div className="flex flex-wrap gap-2.5 pt-1">
          {[
            { tone: "ok", b: "Tier A", t: "analytical · no IRB · tooling live" },
            { tone: "warn", b: "Tier B", t: "exempt determination · fast-track" },
            { tone: "danger", b: "Tier C", t: "full IRB · scoped & gated" },
          ].map((x) => (
            <span
              key={x.b}
              className="inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] bg-white px-3 py-1.5 text-sm text-[#6b7280]"
            >
              <Pip tone={x.tone as "ok" | "warn" | "danger"} />
              <b className="font-semibold text-[#0d1117]">{x.b}</b> — {x.t}
            </span>
          ))}
        </div>
      </section>

      {/* Overview */}
      <section id="overview" className="space-y-5 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            What this study is — and is not
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            A single phrase, &quot;test the performance of this pipeline,&quot; hides three studies
            with very different regulatory burdens. Naming them separately is what lets the un-gated
            science start now while the IRB package is assembled in parallel.
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-2 text-lg text-[#0d1117]" style={serif}>
              It is
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-[0.92rem] text-[#3a3f4a]">
              <li>
                A <b>diagnostic / predictive-accuracy</b> study — <b>observational</b>.
              </li>
              <li>
                Endpoints are <b>software-accuracy metrics</b>: concordance, sensitivity,
                specificity, PPV/NPV, calibration, diplotype concordance vs. an accepted reference
                standard.
              </li>
              <li>
                Reported under <b>STARD 2015</b> (diagnostic accuracy) and <b>TRIPOD-AI / PROBAST-AI</b>{" "}
                (prediction models).
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-2 text-lg text-[#0d1117]" style={serif}>
              It is not
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-[0.92rem] text-[#3a3f4a]">
              <li>
                Not a <b>therapy trial</b>. Administering BPC-157 / TB-500 / etc. to test response is
                an interventional study of an investigational compound — separate, likely needs an FDA
                IND.
              </li>
              <li>
                Not a <b>clinical service</b>. The research pipeline is not CLIA-certified; its
                results cannot be returned for clinical use (see guardrails).
              </li>
              <li>
                Not <b>one IRB submission</b>. The work partitions across three human-subjects tiers.
              </li>
            </ul>
          </div>
        </div>
        <Note>
          <b>The threshold rule (45 CFR 46).</b> An activity needs IRB oversight only if it is{" "}
          <i>research</i> involving <i>human subjects</i> — data obtained through
          intervention/interaction with a living individual, or identifiable private information. Map
          every &quot;performance&quot; question onto one of the three tiers below before assuming an
          IRB is required.
        </Note>
      </section>

      {/* Tiers */}
      <section id="tiers" className="space-y-5 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            The three-tier partition
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            The same partition drives the regulatory pathway <em>and</em> the development order: Tier
            A is the bulk of &quot;does it compute correctly&quot; and is un-gated; Tier C is the only
            track needing the full machinery and is scoped tightly to stay observational.
          </p>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          {[
            {
              tag: "Tier A",
              top: "border-t-[#15803d]",
              h: "Analytical validation",
              q: "Does the pipeline read the genome correctly?",
              items: [
                <>
                  <b>Tests:</b> variant-call concordance, sensitivity/specificity/precision;
                  star-allele diplotype concordance; STR/CAG length; genome-build handling.
                </>,
                <>
                  <b>Data:</b> cell-line &amp; de-identified public truth sets — GIAB/NIST, CDC GeT-RM
                  (Coriell), 1000 Genomes.
                </>,
                <>
                  <b>HS status:</b> <b>Not human subjects</b> — 45 CFR 46.102(e).
                </>,
              ],
              status: { tone: "ok", t: "No IRB · tooling complete, begin now" },
            },
            {
              tag: "Tier B",
              top: "border-t-[#2563eb]",
              h: "Secondary use of existing data",
              q: "Does a call predict a real clinical state?",
              items: [
                <>
                  <b>Tests:</b> interpretation/scoring concordance, PGx phenotype concordance, PRS
                  calibration.
                </>,
                <>
                  <b>Data:</b> already-collected, de-identified/coded clinical genomes &amp; outcomes;
                  biobank / dbGaP under a DUA.
                </>,
                <>
                  <b>HS status:</b> often <b>Exempt</b> — 45 CFR 46.104(d)(4) — or not-HSR.
                </>,
              ],
              status: { tone: "warn", t: "Determination request · DUA likely" },
            },
            {
              tag: "Tier C",
              top: "border-t-[#d97706]",
              h: "Prospective / identifiable",
              q: "Performance on freshly recruited people; any return of results.",
              items: [
                <>
                  <b>Tests:</b> performance on new enrollment; identifiable specimens; longitudinal
                  biomarker tracking on real people.
                </>,
                <>
                  <b>Data:</b> new enrollment, identifiable genomic data.
                </>,
                <>
                  <b>HS status:</b> <b>Human-subjects research.</b>
                </>,
              ],
              status: { tone: "danger", t: "Full IRB submission — protocol, consent, the works" },
            },
          ].map((c) => (
            <div
              key={c.tag}
              className={`rounded-xl border border-t-[3px] border-[#dbd9d3] bg-white p-5 ${c.top}`}
            >
              <div className="text-xs uppercase tracking-[0.1em] text-[#6b7280]">{c.tag}</div>
              <h3 className="mt-1 text-lg text-[#0d1117]" style={serif}>
                {c.h}
              </h3>
              <div className="text-[0.9rem] text-[#6b7280]">{c.q}</div>
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-[0.92rem] text-[#3a3f4a]">
                {c.items.map((it, i) => (
                  <li key={i}>{it}</li>
                ))}
              </ul>
              <span className="mt-3.5 inline-flex items-center gap-2 rounded-full border border-[#dbd9d3] px-3 py-1 text-[0.8rem] text-[#3a3f4a]">
                <Pip tone={c.status.tone as "ok" | "warn" | "danger"} />
                {c.status.t}
              </span>
            </div>
          ))}
        </div>
        <Note>
          <b>Don&apos;t let the IRB self-determine your tiers.</b> For Tiers A &amp; B, file a short
          written determination request (&quot;not human subjects research&quot; / &quot;exempt&quot;)
          and keep the letter on file — that is what protects publications and audits. At UF, the
          self-service <b>Exempt Auto-Determination tool</b> (IRB 850 training) covers the Tier B
          route; a full Tier C study needs IRB 803.
        </Note>
      </section>

      {/* IRB pathway */}
      <section id="irb" className="space-y-5 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            IRB pathway — the one gating decision
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            Everything institution-specific (forms, submission system, training pathway, fees,
            reliance) flows from a single question. It changes the <em>mechanics</em>, not the
            structure of the study.
          </p>
        </div>
        <div className="rounded-xl border border-[#dbd9d3] border-l-[3px] border-l-[#1a6b4a] bg-white p-5">
          <h3 className="text-lg text-[#0d1117]" style={serif}>
            Is this research conducted under the University of Florida&apos;s auspices?
          </h3>
          <div className="text-[0.93rem] text-[#6b7280]">
            — by a UF employee or student, using UF funds, data, or resources/facilities?
          </div>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          {[
            {
              tag: "If yes",
              h: "UF HRPP is the IRB of record",
              items: [
                <>
                  Routes to <b>IRB-01</b> (Gainesville HSC) — all medical research, tissue/data banks,
                  HIPAA data. <b>Not IRB-02</b> (social/behavioral only). Address submissions to the
                  HRPP office via myIRB, not a named chair.
                </>,
                <>
                  UF Innovate already holds a patent disclosure on this pipeline — institutional
                  entanglement worth confirming.
                </>,
              ],
            },
            {
              tag: "If no",
              h: "Commercial / central IRB",
              items: [
                <>Purely Florida Man Bioscience work → a commercial IRB (e.g., Advarra, WCG).</>,
                <>Companies without an internal board contract one.</>,
              ],
            },
            {
              tag: "If both engaged",
              h: "Single-IRB reliance (sIRB)",
              items: [
                <>UF investigator + company sponsor → a reliance agreement.</>,
                <>
                  Vehicles: IRB-01 as the OneFlorida+ consortium IRB, SMART IRB master reliance, or{" "}
                  <b>IRB-04 / WCG</b> commercial cede.
                </>,
              ],
            },
          ].map((c) => (
            <div key={c.tag} className="rounded-xl border border-[#dbd9d3] bg-white p-5">
              <div className="text-xs uppercase tracking-[0.1em] text-[#6b7280]">{c.tag}</div>
              <h3 className="mt-1 text-lg text-[#0d1117]" style={serif}>
                {c.h}
              </h3>
              <ul className="mt-2 list-disc space-y-1.5 pl-5 text-[0.92rem] text-[#3a3f4a]">
                {c.items.map((it, i) => (
                  <li key={i}>{it}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <Note>
          <b>Decision owner:</b> Noah + any UF faculty sponsor. Confirm UF engagement before choosing
          the board. UF is AAHRPP-accredited — expect rigorous documentation regardless of route.
        </Note>
      </section>

      {/* Guardrails */}
      <section id="guardrails" className="space-y-5 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            Design guardrails — settle these before drafting the protocol
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            Each of these is a constraint that shapes consent, budget, and the data-flow diagram. They
            are the things an IRB and COI committee scrutinize hardest; an unaddressed one stalls the
            whole submission.
          </p>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          {[
            {
              icon: "🧬",
              h: "The peptide boundary",
              t: (
                <>
                  Validate the pipeline&apos;s <b>predictions</b> observationally — in existing data,
                  or in participants receiving peptides <i>independently of this study</i>.{" "}
                  <b>Administering</b> peptides to test response is a separate interventional trial
                  (FDA IND, DSMB, multi-year budget). Keep scope on the observational side.
                </>
              ),
            },
            {
              icon: "🔒",
              h: "The CLIA wall",
              t: (
                <>
                  The research pipeline is <b>not CLIA-certified</b>, so its results cannot be returned
                  for clinical use. The protocol must either <b>return nothing</b> (cleanest), or{" "}
                  <b>confirm any actionable finding in a CLIA lab</b> before disclosure, with genetic
                  counseling — material because the default ACMG81 panel surfaces actionable secondary
                  findings.
                </>
              ),
            },
            {
              icon: "⚖️",
              h: "Conflict of interest",
              t: (
                <>
                  The PI holds a <b>UF Innovate patent disclosure on the very pipeline under study</b>.
                  Investigator interest in the technology being validated is the single most-scrutinized
                  issue. Deliverable: a written <b>COI management plan</b> (disclosure to IRB + COI
                  office, independent oversight of analysis, disclosure in consent &amp; publications).
                  Do not submit without it.
                </>
              ),
            },
          ].map((c) => (
            <div
              key={c.h}
              className="rounded-xl border border-[#dbd9d3] border-l-[3px] border-l-[#b91c1c] bg-white p-5"
            >
              <h3 className="mb-2 text-lg text-[#0d1117]" style={serif}>
                <span className="mr-1.5 text-xl">{c.icon}</span>
                {c.h}
              </h3>
              <p className="text-[0.92rem] text-[#3a3f4a]">{c.t}</p>
            </div>
          ))}
        </div>
        <Note>
          <b>Plus, for any identifiable genomic data:</b> GINA protections (and their gaps) in consent
          · re-identification risk &amp; a data-security plan · genetic-specific consent (secondary
          use, sharing, future-use, withdrawal limits) · consider an NIH{" "}
          <b>Certificate of Confidentiality</b> (free). Note a current launch-blocker: the API must
          have auth + encryption at rest before identifiable data can legally flow through it.
        </Note>
      </section>

      {/* Roadmap */}
      <section id="roadmap" className="space-y-5 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            Development roadmap
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            The sequence keeps the un-gated science moving while the IRB package is assembled in
            parallel.
          </p>
        </div>
        <ol className="space-y-4">
          {[
            {
              b: "Now — no IRB.",
              t: (
                <>
                  Run Tier A analytical validation against GIAB/GeT-RM. Largest body of performance
                  evidence; needs no approval.{" "}
                  <span className="text-[#15803d]">
                    Harness, converters, and panel tooling are built.
                  </span>
                </>
              ),
            },
            {
              b: "Weeks 1–4.",
              t: (
                <>
                  Confirm IRB of record. File the Tier B determination/exemption request for
                  retrospective de-identified data. Complete training. Draft the COI management plan.
                </>
              ),
            },
            {
              b: "Weeks 2–8 (parallel).",
              t: (
                <>
                  Author the Tier C protocol + consent + data-security + DUA package. Requires the
                  intended-use decision and API security remediation underway.
                </>
              ),
            },
            {
              b: "Submit Tier C → IRB review.",
              t: (
                <>
                  Expect revisions; genetic + COI studies draw scrutiny. Do not enroll or touch
                  identifiable data until approval.
                </>
              ),
            },
            {
              b: "Maintain.",
              t: (
                <>
                  Continuing review/renewals, amendments, adverse-event / unanticipated-problem
                  reporting.
                </>
              ),
            },
          ].map((s, i) => (
            <li key={i} className="flex gap-4">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[#dbd9d3] bg-[#edecea] text-sm text-[#1a6b4a]">
                {i + 1}
              </span>
              <p className="text-[0.95rem] text-[#3a3f4a]">
                <b className="text-[#0d1117]">{s.b}</b> {s.t}
              </p>
            </li>
          ))}
        </ol>

        <div className="grid gap-5 sm:grid-cols-2">
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-2 text-lg text-[#0d1117]" style={serif}>
              🔴 Only-you / human actions
            </h3>
            <ul className="space-y-2.5 text-[0.93rem] text-[#3a3f4a]">
              {[
                "Confirm UF engagement & choose the IRB of record.",
                "Sign the COI disclosure (coi.ufl.edu) & own the management plan.",
                "Decide the return-of-results posture & the peptide scope boundary.",
                "Complete IRB 803 training; secure a qualified PI / faculty sponsor.",
                "All IRB submissions, signatures & HRPP communications.",
              ].map((t, i) => (
                <li key={i} className="flex gap-2.5">
                  <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded border border-[#b91c1c] bg-[#b91c1c]/10 text-[0.7rem] text-[#b91c1c]">
                    !
                  </span>
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-2 text-lg text-[#0d1117]" style={serif}>
              🟢 Drafted / built for you
            </h3>
            <ul className="space-y-2.5 text-[0.93rem] text-[#3a3f4a]">
              {[
                { done: true, t: "Tier A analytical-validation harness (concordance / sensitivity / specificity)." },
                { done: true, t: "GIAB & GeT-RM reference converters + panel-site distillation tooling." },
                { done: true, t: "Tier A/B determination-request memo for the IRB office." },
                { done: false, t: "First drafts: protocol, data-management & security plan, genetic consent language." },
                { done: false, t: "API security remediation (auth + encryption) gating identifiable-data studies." },
              ].map((x, i) => (
                <li key={i} className="flex gap-2.5">
                  <span
                    className={`mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded border text-[0.7rem] ${
                      x.done
                        ? "border-[#15803d] bg-[#15803d]/10 text-[#15803d]"
                        : "border-[#d97706] bg-[#d97706]/10 text-[#d97706]"
                    }`}
                  >
                    {x.done ? "✓" : "○"}
                  </span>
                  {x.t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Endpoints */}
      <section id="endpoints" className="space-y-4 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            Endpoints &amp; reference standards
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            Primary endpoints are concordance/accuracy against an accepted reference. Each tier
            compares pipeline output to a fixed, versioned truth set.
          </p>
        </div>
        <div className="overflow-x-auto rounded-xl border border-[#dbd9d3] bg-white">
          <table className="w-full text-left text-[0.92rem]">
            <thead>
              <tr className="border-b border-[#dbd9d3] text-xs uppercase tracking-[0.06em] text-[#6b7280]">
                <th className="p-3 font-semibold">Pipeline output</th>
                <th className="p-3 font-semibold">Reference standard</th>
                <th className="p-3 font-semibold">Metric</th>
                <th className="p-3 font-semibold">Tier</th>
              </tr>
            </thead>
            <tbody className="text-[#3a3f4a]">
              {[
                ["Variant calls (genotype)", "GIAB/NIST high-confidence benchmark VCFs", "Sensitivity, specificity, precision, F1, genotype concordance", "A"],
                ["PGx star-allele diplotypes", "CDC GeT-RM consensus (Coriell cell lines)", "Diplotype + phenotype concordance", "A"],
                ["STR / AR-CAG repeat length", "Validated repeat-length references", "Length accuracy; interpretation verification", "A"],
                ["Variant interpretation / classification", "Expert-panel ClinVar / ClinGen", "Classification concordance", "B"],
                ["PGx phenotype & polygenic scores", "CPIC reference diplotypes; measured outcomes", "Phenotype concordance; PRS calibration", "B"],
                ["Predictive “responder” calls", "Measured biomarker trajectories in enrolled participants", "Predictive accuracy (STARD / TRIPOD-AI)", "C"],
              ].map((row, i) => (
                <tr key={i} className="border-b border-[#dbd9d3] last:border-0">
                  {row.map((cell, j) => (
                    <td key={j} className="p-3 align-top">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Status */}
      <section id="status" className="space-y-4 scroll-mt-20">
        <div>
          <h2 className="text-2xl text-[#0d1117]" style={serif}>
            Live status
          </h2>
          <p className="mt-1 max-w-[70ch] text-[#6b7280]">
            Where the validation program stands today — so protocol drafting can reference real
            readiness, not aspiration.
          </p>
        </div>
        <div className="overflow-x-auto rounded-xl border border-[#dbd9d3] bg-white">
          <table className="w-full text-left text-[0.92rem]">
            <thead>
              <tr className="border-b border-[#dbd9d3] text-xs uppercase tracking-[0.06em] text-[#6b7280]">
                <th className="p-3 font-semibold">Workstream</th>
                <th className="p-3 font-semibold">State</th>
                <th className="p-3 font-semibold">Note</th>
              </tr>
            </thead>
            <tbody className="text-[#3a3f4a]">
              {[
                { w: "Tier A concordance harness + metrics", tone: "ok", s: "Built", n: "Runner, confusion-matrix & categorical metrics, offline-tested" },
                { w: "Reference-data tooling (GIAB / GeT-RM / panel)", tone: "ok", s: "Built", n: "Converters + panel distillation; local-only data policy set" },
                { w: "Genome-build & STR control gates", tone: "ok", s: "Built", n: "Wired as CI regression gates" },
                { w: "Tier A/B determination memo", tone: "ok", s: "Drafted", n: "NHSR (A) + Exempt (B), with regulatory citations" },
                { w: "Reference data acquisition (run the numbers)", tone: "warn", s: "Operator", n: "Download GeT-RM/GIAB, run converters, produce concordance report" },
                { w: "IRB of record decision", tone: "warn", s: "Pending", n: "Human decision — confirm UF engagement" },
                { w: "COI management plan", tone: "warn", s: "Pending", n: "Required before Tier C submission" },
                { w: "API security remediation (auth + encryption)", tone: "danger", s: "Blocker", n: "Gates any identifiable-data (Tier C) flow" },
                { w: "Tier C protocol + consent package", tone: "danger", s: "Not started", n: "Draftable in parallel once intended-use decided" },
              ].map((r, i) => (
                <tr key={i} className="border-b border-[#dbd9d3] last:border-0">
                  <td className="p-3 align-top">{r.w}</td>
                  <td className="p-3 align-top whitespace-nowrap">
                    <span className="inline-flex items-center gap-2">
                      <Pip tone={r.tone as "ok" | "warn" | "danger"} />
                      {r.s}
                    </span>
                  </td>
                  <td className="p-3 align-top">{r.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Footer */}
      <footer className="space-y-3.5 border-t border-[#dbd9d3] pt-6 text-sm text-[#6b7280]">
        <div className="rounded-xl border border-[#dbd9d3] bg-white px-4 py-4">
          <b className="text-[#0d1117]">Planning artifact — not regulatory advice.</b> This hub
          operationalizes the project&apos;s IRB and validation planning documents. The
          institution&apos;s Human Research Protection Program / IRB office and regulatory counsel are
          the authorities of record. No clinical claim is made; no result described here is returned
          to any individual.
        </div>
        <div>
          <div className="mb-1.5 text-[#0d1117]">Source documents</div>
          <div className="flex flex-wrap gap-2">
            {[
              "docs/irb-setup-plan.md",
              "docs/irb-determination-request.md",
              "docs/clinical-validation-plan.md",
              "validation/tier_a/",
              "validation/reference/ACQUISITION.md",
            ].map((c) => (
              <code
                key={c}
                className="rounded border border-[#dbd9d3] bg-[#edecea] px-1.5 py-0.5 text-[#6b7280]"
              >
                {c}
              </code>
            ))}
          </div>
        </div>
        <div>
          Standards: Common Rule 45 CFR 46 · ICH-GCP E6(R3) · HIPAA · GINA · STARD 2015 · TRIPOD-AI /
          PROBAST-AI · GA4GH
        </div>
        <p>
          Participant-facing page:{" "}
          <Link className="text-[#1a6b4a] underline" href="/study">
            the public study site
          </Link>
          .
        </p>
      </footer>
    </div>
  );
}
