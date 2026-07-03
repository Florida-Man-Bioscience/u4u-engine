"use client";

/**
 * Onboarding wizard for a newly genome-uploaded patient.
 *
 * Three sequential stages, surfaced as a single page so the user can
 * see the whole flow at once and scroll back without losing context:
 *
 *   1. Pick a peptide
 *      — Engine recommendations from the /analyze job, ranked by tier,
 *        annotated with PharmGKB-evidence badges where applicable.
 *
 *   2. Record baseline biomarkers
 *      — The chosen peptide's biomarker panel is fetched and rendered
 *        as a numeric-input table. Submitting writes pre-treatment
 *        measurements AND opens a Treatment row (start_date=today) so
 *        the Bayesian model has a week-0 anchor.
 *
 *   3. Projected response
 *      — Calls /tracking/patients/{id}/predictions for each biomarker
 *        in the panel and shows the prior predictive trajectory the
 *        patient should see if they're an average responder for their
 *        genotype.
 *
 * Stages 2 and 3 unlock progressively — there's no point asking for
 * baselines before the peptide is chosen.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

import { getJobStatus } from "../../../../lib/api";
import {
  createMeasurement,
  createTreatment,
  getBiomarkerCatalog,
  getPatient,
  getPrediction,
} from "../../../lib/api";
import type {
  BiomarkerCatalogEntry,
  Patient,
  PredictionResult,
} from "../../../lib/types";
import type { EngineRecommendation } from "../../../../lib/api";
import { PosteriorChart } from "../../../components/PosteriorChart";

interface BaselineEntry {
  value: string; // string so the input can be empty
  unit: string;
}

const TIER_BADGE: Record<string, string> = {
  "Strong Fit": "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Possible Fit": "bg-emerald-50 text-emerald-700 border-emerald-200",
  Baseline: "bg-slate-100 text-slate-600 border-slate-200",
  "Possibly Altered": "bg-amber-100 text-amber-800 border-amber-300",
  "Review Recommended": "bg-amber-100 text-amber-800 border-amber-300",
  "Review Needed": "bg-amber-100 text-amber-800 border-amber-300",
  "Likely Reduced": "bg-rose-100 text-rose-800 border-rose-300",
  "Altered / Reduced": "bg-rose-100 text-rose-800 border-rose-300",
  Caution: "bg-rose-200 text-rose-900 border-rose-400",
};

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function OnboardingPage() {
  const router = useRouter();
  const params = useParams();
  const search = useSearchParams();
  const patientId = params.id as string;
  const jobId = search.get("from_job");

  // ── Stage 0: load patient + engine recommendations ──────────────────────
  const [patient, setPatient] = useState<Patient | null>(null);
  const [recs, setRecs] = useState<EngineRecommendation[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await getPatient(patientId);
        if (!cancelled) setPatient(p);
      } catch (err) {
        if (!cancelled)
          setLoadError(
            err instanceof Error ? err.message : "Failed to load patient.",
          );
        return;
      }
      if (!jobId) {
        if (!cancelled) setRecs([]);
        return;
      }
      try {
        const job = await getJobStatus(jobId);
        const raw =
          (job.results?.peptide_recommendations?.recommendations as
            | Array<Record<string, unknown>>
            | undefined) ?? [];
        const tierRank = (t: string | null | undefined): number =>
          ({
            "Strong Fit": 0,
            "Possible Fit": 1,
            Baseline: 2,
            "Possibly Altered": 3,
            "Review Recommended": 4,
            "Review Needed": 4,
            "Likely Reduced": 5,
            "Altered / Reduced": 5,
            Caution: 6,
          })[t ?? ""] ?? 7;
        const ranked: EngineRecommendation[] = raw
          .map((r) => ({
            peptide_name: String(r.peptide_name ?? ""),
            category: (r.category as string | null) ?? null,
            predicted_tier: (r.predicted_tier as string | null) ?? null,
            prediction_description:
              (r.prediction_description as string | null) ?? null,
            has_pharmgkb_evidence: false,
            has_patient_signal: false,
          }))
          .filter((r) => r.peptide_name)
          .sort((a, b) => tierRank(a.predicted_tier) - tierRank(b.predicted_tier));
        if (!cancelled) setRecs(ranked);
      } catch (err) {
        if (!cancelled)
          setLoadError(
            err instanceof Error
              ? err.message
              : "Failed to load engine recommendations.",
          );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [patientId, jobId]);

  // ── Stage 1: peptide selection ──────────────────────────────────────────
  const [pickedPeptide, setPickedPeptide] = useState<string | null>(null);
  const [panel, setPanel] = useState<BiomarkerCatalogEntry[] | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);

  useEffect(() => {
    setPanel(null);
    setPanelError(null);
    if (!pickedPeptide) return;
    let cancelled = false;
    getBiomarkerCatalog(pickedPeptide)
      .then((p) => {
        if (!cancelled) setPanel(p);
      })
      .catch((err) => {
        if (!cancelled)
          setPanelError(
            err instanceof Error
              ? err.message
              : "Failed to load biomarker panel.",
          );
      });
    return () => {
      cancelled = true;
    };
  }, [pickedPeptide]);

  // ── Stage 2: baseline entry ─────────────────────────────────────────────
  const [baselines, setBaselines] = useState<Record<string, BaselineEntry>>({});
  const [baselineSaving, setBaselineSaving] = useState(false);
  const [baselineError, setBaselineError] = useState<string | null>(null);
  const [baselinesSaved, setBaselinesSaved] = useState(false);

  useEffect(() => {
    if (!panel) {
      setBaselines({});
      return;
    }
    // Pre-seed the unit cell from the panel's catalog default so the
    // user only has to type a number.
    setBaselines(
      Object.fromEntries(
        panel.map((b) => [
          b.name,
          { value: "", unit: b.unit ?? "" } as BaselineEntry,
        ]),
      ),
    );
    setBaselinesSaved(false);
  }, [panel]);

  const handleSubmitBaselines = useCallback(async () => {
    if (!pickedPeptide || !panel) return;
    const entries = Object.entries(baselines).filter(([, v]) =>
      v.value.trim() !== "",
    );
    if (entries.length === 0) {
      setBaselineError(
        "Enter at least one baseline measurement before continuing.",
      );
      return;
    }
    setBaselineError(null);
    setBaselineSaving(true);
    try {
      // 1) Open a treatment row at today so the Bayesian model has a
      //    week-0 anchor. The user can edit dose/schedule later from
      //    the patient page.
      const start = todayIso();
      const treatment = await createTreatment(patientId, {
        peptide_name: pickedPeptide,
        start_date: start,
        dose: null,
        dose_unit: null,
        schedule: null,
        route: null,
        end_date: null,
        notes: "Onboarding placeholder — edit dose/schedule on the patient page.",
      });
      // 2) Write each non-empty baseline as a measurement at start_date.
      //    They'll be picked up by the Bayesian baseline window upstream.
      for (const [name, entry] of entries) {
        const v = Number(entry.value);
        if (!Number.isFinite(v)) continue;
        await createMeasurement({
          patient_id: patientId,
          biomarker_name: name,
          value: v,
          measured_at: start,
          treatment_id: treatment.id,
          unit: entry.unit || null,
        });
      }
      setBaselinesSaved(true);
    } catch (err) {
      setBaselineError(
        err instanceof Error
          ? err.message
          : "Failed to save baselines. Please retry.",
      );
    } finally {
      setBaselineSaving(false);
    }
  }, [baselines, panel, patientId, pickedPeptide]);

  // ── Stage 3: projected response ─────────────────────────────────────────
  const [predictions, setPredictions] = useState<
    Record<string, PredictionResult>
  >({});
  const [predictError, setPredictError] = useState<string | null>(null);

  useEffect(() => {
    if (!baselinesSaved || !pickedPeptide || !panel) return;
    let cancelled = false;
    (async () => {
      try {
        const out: Record<string, PredictionResult> = {};
        for (const b of panel) {
          try {
            const pred = await getPrediction(patientId, pickedPeptide, b.name);
            out[b.name] = pred;
          } catch {
            // Skip biomarkers the predictor can't fit (e.g. unsupported
            // panel entry) — surface what we can.
          }
        }
        if (!cancelled) setPredictions(out);
      } catch (err) {
        if (!cancelled)
          setPredictError(
            err instanceof Error
              ? err.message
              : "Failed to compute projections.",
          );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [baselinesSaved, panel, patientId, pickedPeptide]);

  // ── Computed convenience views ──────────────────────────────────────────
  const topRecs = useMemo(() => recs?.slice(0, 6) ?? [], [recs]);

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <header className="flex items-baseline justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Onboarding{patient ? ` — ${patient.label}` : ""}
          </h1>
          <p className="text-sm text-slate-600">
            Three steps: pick a peptide based on the genetic analysis,
            record baseline labs, see the projected response under
            average-responder assumptions.
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.push(`/tracking/patients/${patientId}`)}
          className="text-xs text-slate-500 underline hover:text-slate-700"
        >
          Skip to patient page →
        </button>
      </header>

      {loadError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {loadError}
        </div>
      )}

      {/* ── Stage 1 ────────────────────────────────────────────── */}
      <Section
        index={1}
        title="Recommended peptides"
        subtitle={
          jobId
            ? "Ranked by the engine's per-peptide variant analysis from the genome upload. Pick one to continue."
            : "No source job linked — you can still pick any peptide manually."
        }
      >
        {!recs && <p className="text-sm text-slate-500">Loading…</p>}
        {recs && recs.length === 0 && (
          <p className="text-sm text-slate-500">
            No peptide recommendations came back from the analysis job.
          </p>
        )}
        {topRecs.length > 0 && (
          <div className="grid gap-2 sm:grid-cols-2">
            {topRecs.map((r) => {
              const picked = pickedPeptide === r.peptide_name;
              const tierClass =
                TIER_BADGE[r.predicted_tier ?? ""] ??
                "bg-slate-100 text-slate-600 border-slate-200";
              return (
                <button
                  key={r.peptide_name}
                  type="button"
                  onClick={() => setPickedPeptide(r.peptide_name)}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    picked
                      ? "border-teal-600 bg-teal-50 ring-2 ring-teal-500"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-900">
                      {r.peptide_name}
                    </span>
                    {r.predicted_tier && (
                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${tierClass}`}
                      >
                        {r.predicted_tier}
                      </span>
                    )}
                  </div>
                  {r.prediction_description && (
                    <p className="mt-1 text-xs text-slate-600">
                      {r.prediction_description}
                    </p>
                  )}
                  {r.category && (
                    <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-400">
                      {r.category}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </Section>

      {/* ── Stage 2 ────────────────────────────────────────────── */}
      <Section
        index={2}
        title="Record baseline biomarkers"
        subtitle={
          pickedPeptide
            ? `Enter pre-treatment values for the ${pickedPeptide} panel. We'll save them as measurements dated today and open a treatment record so the Bayesian model has a week-0 anchor.`
            : "Pick a peptide above to load its biomarker panel."
        }
        locked={!pickedPeptide}
      >
        {pickedPeptide && !panel && !panelError && (
          <p className="text-sm text-slate-500">Loading panel…</p>
        )}
        {panelError && (
          <p className="text-sm text-rose-700">{panelError}</p>
        )}
        {panel && (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3">Biomarker</th>
                  <th className="py-2 pr-3">Modality</th>
                  <th className="py-2 pr-3">Expected direction</th>
                  <th className="py-2 pr-3">Unit</th>
                  <th className="py-2 pr-3">Baseline value</th>
                </tr>
              </thead>
              <tbody>
                {panel.map((b) => {
                  const entry = baselines[b.name] ?? { value: "", unit: b.unit ?? "" };
                  return (
                    <tr key={b.name} className="border-b border-slate-100">
                      <td className="py-2 pr-3 font-medium text-slate-800">
                        {b.name}
                      </td>
                      <td className="py-2 pr-3 text-slate-500">{b.modality}</td>
                      <td className="py-2 pr-3 text-slate-500">{b.direction}</td>
                      <td className="py-2 pr-3 text-slate-500">{b.unit}</td>
                      <td className="py-2 pr-3">
                        <input
                          type="number"
                          step="any"
                          inputMode="decimal"
                          disabled={baselinesSaved || baselineSaving}
                          value={entry.value}
                          onChange={(e) =>
                            setBaselines((s) => ({
                              ...s,
                              [b.name]: { ...entry, value: e.target.value },
                            }))
                          }
                          className="w-32 rounded border border-slate-200 px-2 py-1 text-right text-sm focus:border-teal-500 focus:outline-none disabled:bg-slate-50"
                          placeholder={
                            b.timeframe_weeks_min
                              ? `e.g. by ${b.timeframe_weeks_min}w`
                              : ""
                          }
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {baselineError && (
              <p className="text-sm text-rose-700">{baselineError}</p>
            )}

            {!baselinesSaved ? (
              <button
                type="button"
                onClick={handleSubmitBaselines}
                disabled={baselineSaving}
                className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-800 disabled:opacity-50"
              >
                {baselineSaving
                  ? "Saving baselines…"
                  : "Save baselines and project response"}
              </button>
            ) : (
              <p className="text-sm text-teal-800">
                Baselines saved. Projected response below.
              </p>
            )}
          </>
        )}
      </Section>

      {/* ── Stage 3 ────────────────────────────────────────────── */}
      <Section
        index={3}
        title="Projected response"
        subtitle={
          baselinesSaved
            ? `Prior predictive trajectory for each biomarker under average-responder assumptions for this patient's genetics. As real follow-up measurements come in, the Bayesian model will update these toward the observed data.`
            : "Save your baselines above to see the projection."
        }
        locked={!baselinesSaved}
      >
        {baselinesSaved && Object.keys(predictions).length === 0 && (
          <p className="text-sm text-slate-500">Computing projections…</p>
        )}
        {predictError && (
          <p className="text-sm text-rose-700">{predictError}</p>
        )}
        {panel?.map((b) => {
          const pred = predictions[b.name];
          if (!pred) return null;
          // Look up the panel entry to feed expected direction into the
          // shared chart component.
          return (
            <div
              key={b.name}
              className="space-y-2 rounded-lg border border-slate-200 bg-white p-4"
            >
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="font-medium text-slate-800">{b.name}</h3>
                <span className="text-xs text-slate-500">
                  expected {b.direction}
                </span>
              </div>
              <PosteriorChart
                measurements={[]}
                treatmentStartIso={todayIso()}
                expected={b}
                prediction={pred}
              />
            </div>
          );
        })}

        {baselinesSaved && (
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={() => router.push(`/tracking/patients/${patientId}`)}
              className="rounded-lg border border-teal-600 bg-white px-4 py-2 text-sm font-medium text-teal-700 transition-colors hover:bg-teal-50"
            >
              Open patient page →
            </button>
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({
  index,
  title,
  subtitle,
  locked,
  children,
}: {
  index: number;
  title: string;
  subtitle: string;
  locked?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      className={`space-y-3 ${locked ? "opacity-60" : ""}`}
      aria-disabled={locked}
    >
      <div className="flex items-baseline gap-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-700 text-xs font-medium text-white">
          {index}
        </span>
        <h2 className="text-lg font-medium text-slate-900">{title}</h2>
      </div>
      <p className="ml-9 text-sm text-slate-600">{subtitle}</p>
      <div className="ml-9 space-y-3">{children}</div>
    </section>
  );
}
