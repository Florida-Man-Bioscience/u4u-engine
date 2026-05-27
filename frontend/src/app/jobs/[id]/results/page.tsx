"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { getJobStatus } from "../../../lib/api";
import type {
  VariantResult,
  Tier,
  PeptideMapping,
  PeptideRecommendation,
  Bpc157Prediction,
} from "../../../lib/types";
import { VariantCard } from "../../../components/VariantCard";
import { SummaryMetrics } from "../../../components/SummaryMetrics";

const TIER_ORDER: Tier[] = ["critical", "high", "medium", "low"];

type ViewMode = "peptides" | "variants";

const PREDICTED_TIER_COLORS: Record<string, string> = {
  "Strong Fit": "bg-green-100 text-green-800 border-green-300",
  "Altered / Reduced": "bg-yellow-100 text-yellow-800 border-yellow-300",
  Caution: "bg-red-100 text-red-800 border-red-300",
  Baseline: "bg-zinc-100 text-zinc-500 border-zinc-200",
  Unknown: "bg-zinc-100 text-zinc-500 border-zinc-200",
  // BPC-157 specific tiers
  likely_good: "bg-green-100 text-green-800 border-green-300",
  possible: "bg-yellow-100 text-yellow-800 border-yellow-300",
  uncertain: "bg-zinc-100 text-zinc-600 border-zinc-300",
  low_confidence: "bg-red-50 text-red-600 border-red-200",
};

const PREDICTED_TIER_LABELS: Record<string, string> = {
  "Strong Fit": "Strong Fit",
  "Altered / Reduced": "Altered / Reduced",
  Caution: "Caution",
  Baseline: "Baseline",
  Unknown: "Unknown",
  likely_good: "Likely Good Candidate",
  possible: "Possible Candidate",
  uncertain: "Uncertain",
  low_confidence: "Low Confidence",
};

export default function ResultsPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;

  const [results, setResults] = useState<VariantResult[] | null>(null);
  const [peptides, setPeptides] = useState<PeptideMapping | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tierFilter, setTierFilter] = useState<Tier | "all">("all");
  const [viewMode, setViewMode] = useState<ViewMode>("peptides");

  useEffect(() => {
    getJobStatus(jobId)
      .then((data) => {
        if (data.results) {
          const res = data.results;
          if (res.variants) {
            setResults(res.variants);
          } else {
            setError("Results not available. The job may still be running.");
          }
          if (res.peptide_recommendations) {
            setPeptides(res.peptide_recommendations);
          }
        } else {
          setError("Results not available. The job may still be running.");
        }
      })
      .catch((err: unknown) =>
        setError(
          err instanceof Error ? err.message : "Failed to load results."
        )
      );
  }, [jobId]);

  const downloadCsv = useCallback(() => {
    if (!results) return;

    const headers = [
      "variant_id",
      "rsid",
      "location",
      "genes",
      "consequence",
      "tier",
      "score",
      "clinvar",
      "disease_name",
      "gnomad_af",
      "headline",
    ];

    const rows = results.map((r) =>
      [
        r.variant_id,
        r.rsid ?? "",
        r.location,
        r.genes.join(";"),
        r.consequence,
        r.tier,
        r.score,
        r.clinvar ?? "",
        r.disease_name ?? "",
        r.gnomad_af ?? "",
        `"${r.headline.replace(/"/g, '""')}"`,
      ].join(",")
    );

    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `variants-${jobId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [results, jobId]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-center max-w-md space-y-4">
          <p className="text-red-700 font-medium">Failed to load results</p>
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="rounded-lg bg-blue-700 text-white px-5 py-2 text-sm font-medium hover:bg-blue-800 transition-colors"
          >
            Back to upload
          </button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-2 text-zinc-500">
          <span className="inline-block h-5 w-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
          Loading results…
        </div>
      </div>
    );
  }

  const filtered =
    tierFilter === "all"
      ? results
      : results.filter((r) => r.tier === tierFilter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Variant Report</h1>
          <p className="text-sm text-zinc-500 font-mono mt-0.5">{jobId}</p>
        </div>
        <button
          onClick={downloadCsv}
          className="rounded-lg border border-zinc-200 bg-white text-zinc-700 px-4 py-2 text-sm font-medium hover:bg-zinc-50 transition-colors"
        >
          ⬇ Download CSV
        </button>
      </div>

      {/* Summary metrics */}
      <SummaryMetrics results={results} />

      {/* View mode toggle */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setViewMode("peptides")}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            viewMode === "peptides"
              ? "bg-blue-700 text-white"
              : "bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
          }`}
        >
          Peptide Therapies
          {peptides && ` (${peptides.recommendations.length})`}
        </button>
        <button
          onClick={() => setViewMode("variants")}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            viewMode === "variants"
              ? "bg-blue-700 text-white"
              : "bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
          }`}
        >
          All Variants ({results.length})
        </button>
      </div>

      {/* ── Peptide Therapies View ─────────────────────────────────────────── */}
      {viewMode === "peptides" && peptides && (
        <div className="space-y-3">
          <p className="text-sm text-zinc-600 leading-relaxed">
            {peptides.summary_text}
          </p>
          {peptides.recommendations.map((rec) => (
            <PeptideTherapyCard key={rec.peptide_name} recommendation={rec} />
          ))}
        </div>
      )}

      {/* ── All Variants View ──────────────────────────────────────────────── */}
      {viewMode === "variants" && (
        <>
          {/* Tier filter */}
          <div className="flex flex-wrap gap-2">
            {(["all", ...TIER_ORDER] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTierFilter(t)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors capitalize ${
                  tierFilter === t
                    ? "bg-blue-700 text-white"
                    : "bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                }`}
              >
                {t === "all"
                  ? `All (${results.length})`
                  : `${t} (${results.filter((r) => r.tier === t).length})`}
              </button>
            ))}
          </div>

          {/* Variant cards */}
          {filtered.length === 0 ? (
            <div className="text-center py-16 text-zinc-400">
              No variants match the selected filter.
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((v) => (
                <VariantCard key={v.variant_id} variant={v} />
              ))}
            </div>
          )}
        </>
      )}

      <p className="text-center text-xs text-zinc-400 pb-8">
        {viewMode === "variants"
          ? `${filtered.length} of ${results.length} variants shown`
          : `${peptides?.recommendations.length ?? 0} peptide therapies evaluated`}{" "}
        ·{" "}
        <button
          onClick={() => router.push("/")}
          className="underline hover:no-underline"
        >
          Run another analysis
        </button>
      </p>
    </div>
  );
}

/* ── Peptide Therapy Card ──────────────────────────────────────────────── */

function PeptideTherapyCard({
  recommendation: rec,
}: {
  recommendation: PeptideRecommendation;
}) {
  const [expanded, setExpanded] = useState(false);

  const tierColor =
    PREDICTED_TIER_COLORS[rec.predicted_tier] ??
    PREDICTED_TIER_COLORS.Baseline;
  const tierLabel =
    PREDICTED_TIER_LABELS[rec.predicted_tier] ?? rec.predicted_tier;

  const variantCount = rec.relevant_variants?.length ?? 0;
  const bpc = rec.bpc157_prediction;

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-zinc-50 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xl shrink-0">💊</span>
          <div className="min-w-0">
            <h2 className="font-semibold text-zinc-900 text-sm">
              {rec.peptide_name}
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5 truncate">
              {rec.category_display}
              {variantCount > 0 && (
                <span className="ml-2 text-zinc-400">
                  · {variantCount} variant{variantCount !== 1 ? "s" : ""}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${tierColor}`}
          >
            {tierLabel}
          </span>
          <span className="text-zinc-400 text-sm">
            {expanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-zinc-100 p-5 space-y-5">
          {/* Prediction summary */}
          <p className="text-sm text-zinc-700 leading-relaxed">
            {rec.prediction_description}
          </p>

          {/* Rationale */}
          <div>
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-1.5">
              Rationale
            </h3>
            <p className="text-sm text-zinc-600">{rec.rationale}</p>
          </div>

          {/* Gene coverage badges */}
          <div>
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
              Gene Coverage ({Math.round(rec.coverage * 100)}%)
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {rec.genes_for_genotyping.map((gene) => {
                const found = rec.genes_found.includes(gene);
                return (
                  <span
                    key={gene}
                    className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-mono ${
                      found
                        ? "bg-green-50 text-green-700 border border-green-200"
                        : "bg-zinc-50 text-zinc-400 border border-zinc-200"
                    }`}
                  >
                    {found ? "✓" : "○"} {gene}
                  </span>
                );
              })}
            </div>
          </div>

          {/* BPC-157 specific: pathways affected */}
          {bpc && bpc.pathways_affected.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
                Pathways Affected
              </h3>
              <div className="space-y-2">
                {bpc.pathways_affected.map((p) => (
                  <div key={p.pathway} className="flex items-start gap-2 text-sm">
                    <span className="text-blue-500 mt-0.5">●</span>
                    <div>
                      <span className="font-medium text-zinc-800">
                        {p.display_name}
                      </span>
                      <span className="text-zinc-400 ml-1.5">
                        ({p.genes_hit.join(", ")} —{" "}
                        {Math.round(p.coverage * 100)}% coverage)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* BPC-157 specific: genetic modifiers */}
          {bpc && bpc.candidate_factors.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
                Genetic Modifiers Detected
              </h3>
              <div className="space-y-1.5">
                {bpc.candidate_factors.map((f) => (
                  <div key={f.rsid} className="text-sm text-zinc-700">
                    <span className="font-mono text-xs bg-zinc-100 px-1 py-0.5 rounded">
                      {f.rsid}
                    </span>{" "}
                    <span className="text-zinc-500">({f.gene})</span> —{" "}
                    {f.effect}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* BPC-157 specific: biomarker recommendations */}
          {bpc && bpc.biomarker_recommendations.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
                Recommended Biomarker Panel
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {bpc.biomarker_recommendations.map((b) => (
                  <div
                    key={b.name}
                    className="flex items-center justify-between text-sm bg-zinc-50 rounded px-3 py-1.5"
                  >
                    <span className="text-zinc-700">{b.name}</span>
                    <span className="text-xs text-zinc-400">
                      {b.expected_change}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Relevant variants */}
          {variantCount > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
                Relevant Gene Variants ({variantCount})
              </h3>
              <div className="space-y-3">
                {rec.relevant_variants.map((v) => (
                  <VariantCard key={v.variant_id} variant={v} />
                ))}
              </div>
            </div>
          )}

          {variantCount === 0 && (
            <div className="text-sm text-zinc-400 text-center py-4 bg-zinc-50 rounded-lg">
              No variants detected in this peptide&apos;s target genes.
            </div>
          )}

          {/* BPC-157 disclaimer */}
          {bpc && (
            <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3">
              <p className="text-xs text-amber-800 leading-relaxed">
                <strong>⚠️ Important:</strong> {bpc.disclaimer}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
