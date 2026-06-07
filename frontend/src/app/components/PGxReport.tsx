"use client";

import { useState } from "react";
import type {
  PGxProfile,
  StarAlleleCall,
  HLACall,
  DrugRecommendation,
  PRSResult,
  DrugPrediction,
  PGxPhenotype,
} from "../lib/types";

/* ─── Visual helpers ────────────────────────────────────────────────────── */

const PHENO_COLOR: Record<PGxPhenotype, string> = {
  PM: "bg-red-100 text-red-800 border-red-300",
  IM: "bg-amber-100 text-amber-800 border-amber-300",
  NM: "bg-green-100 text-green-800 border-green-300",
  RM: "bg-blue-100 text-blue-800 border-blue-300",
  UM: "bg-purple-100 text-purple-800 border-purple-300",
  IND: "bg-zinc-100 text-zinc-600 border-zinc-300",
};

const PHENO_LABEL: Record<PGxPhenotype, string> = {
  PM: "Poor Metabolizer",
  IM: "Intermediate Metabolizer",
  NM: "Normal Metabolizer",
  RM: "Rapid Metabolizer",
  UM: "Ultra-rapid Metabolizer",
  IND: "Indeterminate",
};

const CLASS_COLOR: Record<string, string> = {
  strong: "bg-red-50 text-red-800 border-red-200",
  moderate: "bg-amber-50 text-amber-800 border-amber-200",
  optional: "bg-zinc-50 text-zinc-700 border-zinc-200",
};

const TIER_COLOR: Record<string, string> = {
  high: "bg-red-100 text-red-800 border-red-300",
  intermediate: "bg-amber-100 text-amber-800 border-amber-300",
  low: "bg-green-100 text-green-800 border-green-300",
};

function formatTrait(t: string) {
  return t
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

function setBadge(s: string): { label: string; cls: string } {
  if (s === "respond") return { label: "Responder", cls: "bg-green-100 text-green-800 border-green-300" };
  if (s === "non_respond") return { label: "Non-Responder", cls: "bg-red-100 text-red-800 border-red-300" };
  return { label: "Indeterminate", cls: "bg-zinc-100 text-zinc-600 border-zinc-300" };
}

/* ─── Main component ────────────────────────────────────────────────────── */

export function PGxReport({ profile }: { profile: PGxProfile }) {
  return (
    <div className="space-y-6">
      <SummaryBanner profile={profile} />

      {profile.phenoconversion_notes.length > 0 && (
        <PhenoconversionPanel notes={profile.phenoconversion_notes} />
      )}

      <Section title="Drug-Specific Recommendations" subtitle="CPIC + DPWG curated guidelines applied to your genotype">
        {profile.recommendations.length === 0 ? (
          <EmptyState text="No actionable drug recommendations triggered by your variants." />
        ) : (
          <div className="space-y-2">
            {profile.recommendations.map((r, i) => (
              <RecommendationRow key={`${r.drug}-${r.gene}-${i}`} rec={r} />
            ))}
          </div>
        )}
      </Section>

      <Section title="Drug Response Predictions" subtitle="Heterogeneous-graph ranker with Mondrian conformal prediction sets (90% confidence)">
        {profile.drug_predictions.length === 0 ? (
          <EmptyState text="No drugs evaluated." />
        ) : (
          <DrugPredictionTable predictions={profile.drug_predictions} />
        )}
      </Section>

      <Section title="Pharmacogene Phenotypes" subtitle="Star-allele diplotypes resolved into CPIC metabolizer phenotypes">
        <StarAlleleGrid calls={profile.star_alleles} />
      </Section>

      <Section title="HLA Risk Alleles" subtitle="Tag-SNP detection of HLA alleles linked to severe drug hypersensitivity">
        <HLAGrid calls={profile.hla_calls} />
      </Section>

      <Section title="Pharmacogenomic Polygenic Risk Scores" subtitle="Drug-specific PRS supplementing monogenic predictions">
        {profile.prs_results.length === 0 ? (
          <EmptyState text="No PRS computed — insufficient variant coverage." />
        ) : (
          <PRSTable results={profile.prs_results} />
        )}
      </Section>

      <MethodsFootnote inputPath={profile.input_path} />
    </div>
  );
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

function SummaryBanner({ profile }: { profile: PGxProfile }) {
  const actionable = profile.star_alleles.filter(
    (s) => s.phenotype !== "NM" && s.phenotype !== "IND"
  ).length;
  const hlaPresent = profile.hla_calls.filter((h) => h.present).length;
  const strongRecs = profile.recommendations.filter(
    (r) => r.classification === "strong"
  ).length;

  return (
    <div className="rounded-xl border border-[#1a6b4a]/30 bg-gradient-to-br from-[#1a6b4a]/5 to-transparent p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">🧬</span>
        <h2 className="font-semibold text-zinc-900 text-sm">
          Pharmacogenomics Profile
        </h2>
      </div>
      <p className="text-sm text-zinc-700 leading-relaxed mb-4">
        {profile.summary_text}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Metric label="Actionable phenotypes" value={actionable} />
        <Metric label="HLA risk alleles" value={hlaPresent} />
        <Metric label="Strong recommendations" value={strongRecs} />
        <Metric label="Drugs evaluated" value={profile.drug_predictions.length} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-lg border border-zinc-200 px-3 py-2">
      <p className="text-2xl font-semibold text-[#1a6b4a]">{value}</p>
      <p className="text-xs text-zinc-500 mt-0.5 leading-snug">{label}</p>
    </div>
  );
}

function PhenoconversionPanel({ notes }: { notes: string[] }) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-start gap-2">
        <span className="text-amber-700 text-base shrink-0">⚠</span>
        <div className="space-y-2">
          <p className="text-sm font-semibold text-amber-900">
            Drug–Drug–Gene Phenoconversion
          </p>
          <p className="text-xs text-amber-800 leading-relaxed">
            Your current medications interact with one or more CYP enzymes,
            shifting your effective phenotype. Recommendations below already
            account for this.
          </p>
          <ul className="space-y-1 mt-2">
            {notes.map((n, i) => (
              <li key={i} className="text-xs text-amber-900 flex gap-2">
                <span className="text-amber-600 shrink-0">•</span>
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2">
      <header>
        <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>
        {subtitle && <p className="text-xs text-zinc-500 mt-0.5">{subtitle}</p>}
      </header>
      {children}
    </section>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-200 bg-zinc-50 px-4 py-6 text-center">
      <p className="text-sm text-zinc-500">{text}</p>
    </div>
  );
}

function RecommendationRow({ rec }: { rec: DrugRecommendation }) {
  const cls = CLASS_COLOR[rec.classification] ?? CLASS_COLOR.optional;
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-zinc-900 capitalize text-sm">
              {rec.drug}
            </p>
            <span className="text-xs text-zinc-500 font-mono">
              {rec.gene}
              {rec.phenotype !== "IND" && ` · ${rec.phenotype}`}
            </span>
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide whitespace-nowrap ${cls}`}
        >
          {rec.classification}
        </span>
      </div>
      <p className="text-sm text-zinc-700 leading-relaxed">{rec.recommendation}</p>
      {rec.cpic_guideline_id && (
        <p className="text-xs text-zinc-400 font-mono">
          {rec.source} · {rec.cpic_guideline_id}
        </p>
      )}
    </div>
  );
}

function DrugPredictionTable({ predictions }: { predictions: DrugPrediction[] }) {
  // Show drugs with contributing evidence first
  const sorted = [...predictions].sort((a, b) => {
    if (a.contributing_genes.length !== b.contributing_genes.length) {
      return b.contributing_genes.length - a.contributing_genes.length;
    }
    return a.point_score - b.point_score;
  });
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? sorted : sorted.slice(0, 12);

  return (
    <div className="space-y-2">
      <div className="border border-zinc-200 rounded-lg overflow-hidden bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-zinc-50 text-left text-xs text-zinc-500 font-medium">
              <th className="px-3 py-2">Drug</th>
              <th className="px-3 py-2">Prediction Set</th>
              <th className="px-3 py-2">Score</th>
              <th className="px-3 py-2">Contributing Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {visible.map((p) => (
              <tr key={p.drug} className="text-zinc-700">
                <td className="px-3 py-2 capitalize font-medium">{p.drug}</td>
                <td className="px-3 py-2">
                  <div className="flex gap-1 flex-wrap">
                    {p.prediction_set.map((s) => {
                      const b = setBadge(s);
                      return (
                        <span
                          key={s}
                          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${b.cls}`}
                        >
                          {b.label}
                        </span>
                      );
                    })}
                  </div>
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {p.point_score.toFixed(2)}
                </td>
                <td className="px-3 py-2 text-xs text-zinc-500">
                  {p.contributing_genes.length === 0
                    ? "—"
                    : p.contributing_genes.join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length > 12 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-xs text-[#1a6b4a] font-medium hover:underline"
        >
          {showAll ? "Show top 12" : `Show all ${sorted.length} drugs`}
        </button>
      )}
      <p className="text-xs text-zinc-400 leading-relaxed">
        Prediction sets carry a 90% empirical-coverage guarantee via Mondrian
        split-conformal prediction (Papangelou 2025). A set containing both
        labels means the evidence is insufficient to commit to one — a
        clinically defensible &ldquo;we don&rsquo;t know.&rdquo;
      </p>
    </div>
  );
}

function StarAlleleGrid({ calls }: { calls: StarAlleleCall[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {calls.map((c) => {
        const phenoCls = PHENO_COLOR[c.phenotype];
        return (
          <div
            key={c.gene}
            className="bg-white rounded-lg border border-zinc-200 p-3 space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <p className="font-semibold text-zinc-900 text-sm font-mono">
                {c.gene}
              </p>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${phenoCls}`}
                title={PHENO_LABEL[c.phenotype]}
              >
                {c.phenotype}
              </span>
            </div>
            <p className="text-xs text-zinc-600 font-mono">{c.diplotype}</p>
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span>
                {c.activity_score !== null
                  ? `Activity ${c.activity_score.toFixed(2)}`
                  : "—"}
              </span>
              <span className="capitalize">{c.evidence_tier.replace(/-/g, " ")}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function HLAGrid({ calls }: { calls: HLACall[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {calls.map((h) => (
        <div
          key={h.locus}
          className={`rounded-lg border p-3 space-y-1 ${
            h.present
              ? "border-red-300 bg-red-50"
              : "border-zinc-200 bg-white"
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="font-semibold text-zinc-900 text-sm font-mono">
              {h.locus}
            </p>
            {h.present ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700">
                <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
                Present
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs text-zinc-500">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-300" />
                Absent
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-500 font-mono">
            Tag SNP: {h.tag_rsid ?? "—"}
          </p>
          <p className="text-xs text-zinc-600">
            {h.present ? "Avoid: " : "Risk drugs: "}
            <span className="capitalize">{h.risk_drugs.join(", ")}</span>
          </p>
        </div>
      ))}
    </div>
  );
}

function PRSTable({ results }: { results: PRSResult[] }) {
  return (
    <div className="border border-zinc-200 rounded-lg overflow-hidden bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-zinc-50 text-left text-xs text-zinc-500 font-medium">
            <th className="px-3 py-2">Trait</th>
            <th className="px-3 py-2">Risk Tier</th>
            <th className="px-3 py-2">Score</th>
            <th className="px-3 py-2">Coverage</th>
            <th className="px-3 py-2">Drug Context</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {results.map((p) => (
            <tr key={p.trait} className="text-zinc-700">
              <td className="px-3 py-2 font-medium">{formatTrait(p.trait)}</td>
              <td className="px-3 py-2">
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${TIER_COLOR[p.risk_tier]}`}
                >
                  {p.risk_tier}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-xs">{p.score.toFixed(2)}</td>
              <td className="px-3 py-2 text-xs text-zinc-500">
                {p.n_variants_used}/{p.n_variants_expected} SNPs
              </td>
              <td className="px-3 py-2 text-xs text-zinc-600 capitalize">
                {p.drug_context.join(", ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MethodsFootnote({ inputPath }: { inputPath: string }) {
  const label =
    inputPath === "bam_lr"
      ? "long-read BAM (phased)"
      : inputPath === "bam_sr"
        ? "short-read BAM (Aldy/PyPGx consensus)"
        : "array/VCF (named-allele matcher)";
  return (
    <div className="rounded-md bg-zinc-50 border border-zinc-200 px-4 py-3">
      <p className="text-xs text-zinc-600 leading-relaxed">
        <strong>Methods:</strong> Star alleles called from {label}. CPIC
        activity scores translate diplotypes to PM/IM/NM/RM/UM. Drug–drug–gene
        phenoconversion applied per Nahid 2025 (JAMA Network Open). Drug
        response predictions use a heterogeneous knowledge graph ranker with
        Mondrian split-conformal prediction (Papangelou 2025). HLA tag SNPs
        for B*57:01, B*15:02, B*58:01, A*31:01, B*13:01.
      </p>
      <p className="text-xs text-zinc-500 mt-2 leading-relaxed">
        <strong>Not medical advice.</strong> All recommendations require
        clinical review by a qualified prescriber.
      </p>
    </div>
  );
}
