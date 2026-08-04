"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { DiagnosticsScatter } from "../components/DiagnosticsScatter";
import { getDiagnostics, listPatients } from "../lib/api";
import type {
  DiagnosticsGroup,
  DiagnosticsResult,
  Patient,
} from "../lib/types";

const TARGET_COVERAGE = 0.95;

function fmtPct(x: number | null, digits = 1): string {
  return x === null ? "—" : `${(x * 100).toFixed(digits)}%`;
}

function fmtNum(x: number | null, digits = 1): string {
  return x === null ? "—" : `${x.toFixed(digits)}%`;
}

/** How far coverage sits from the 95% target → a qualitative tone. */
function coverageTone(coverage: number | null): string {
  if (coverage === null) return "text-slate-400";
  const gap = Math.abs(coverage - TARGET_COVERAGE);
  if (gap <= 0.05) return "text-teal-700";
  if (gap <= 0.15) return "text-amber-600";
  return "text-red-600";
}

function MetricCard({
  label,
  value,
  sub,
  tone = "text-slate-800",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 font-mono text-2xl ${tone}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

function GroupTable({
  title,
  rows,
}: {
  title: string;
  rows: DiagnosticsGroup[];
}) {
  if (rows.length === 0) return null;
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 font-medium text-slate-800">{title}</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-slate-700">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-1 pr-3">Name</th>
              <th className="pr-3">Series</th>
              <th className="pr-3">Points</th>
              <th className="pr-3">95% coverage</th>
              <th className="pr-3">MAE</th>
              <th className="pr-3">RMSE</th>
              <th className="pr-3">Bias</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((g) => (
              <tr key={g.label} className="border-t border-slate-100">
                <td className="py-1 pr-3 font-medium text-slate-800">{g.label}</td>
                <td className="pr-3">{g.n_series}</td>
                <td className="pr-3">{g.n_points}</td>
                <td className={`pr-3 font-mono ${coverageTone(g.coverage_95)}`}>
                  {fmtPct(g.coverage_95)}
                </td>
                <td className="pr-3 font-mono">{fmtNum(g.mae_pct)}</td>
                <td className="pr-3 font-mono">{fmtNum(g.rmse_pct)}</td>
                <td className="pr-3 font-mono">
                  {g.bias_pct === null
                    ? "—"
                    : `${g.bias_pct > 0 ? "+" : ""}${g.bias_pct.toFixed(1)}%`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function DiagnosticsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientId, setPatientId] = useState<string>("");
  const [result, setResult] = useState<DiagnosticsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listPatients()
      .then(setPatients)
      .catch(() => {
        /* patient filter is optional — ignore load failure */
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    getDiagnostics(patientId || undefined)
      .then((r) => {
        setResult(r);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "failed to load"))
      .finally(() => setLoading(false));
  }, [patientId]);

  const overall = result?.overall ?? null;

  const coverageSub = useMemo(() => {
    if (!overall || overall.coverage_95 === null) return "target 95%";
    const gap = overall.coverage_95 - TARGET_COVERAGE;
    if (Math.abs(gap) <= 0.05) return "well-calibrated (target 95%)";
    return gap < 0
      ? "below target — bands too tight"
      : "above target — bands too wide";
  }, [overall]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Model diagnostics</h1>
          <p className="max-w-2xl text-sm text-slate-600">
            How well does the Bayesian response model predict what actually
            happened? Each recorded measurement is held out one at a time, the
            model is refit on the rest, and its prediction for the held-out
            point is scored against the real value (a leave-one-out backtest).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex flex-col text-sm">
            <span className="text-xs text-slate-500">Scope</span>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="rounded border border-slate-300 px-2 py-1"
            >
              <option value="">All patients</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <Link href="/tracking" className="text-sm text-teal-700 underline">
            ← Patients
          </Link>
        </div>
      </header>

      {error && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {loading && <p className="text-sm text-slate-500">Running backtest…</p>}

      {!loading && result && result.n_points === 0 && (
        <p className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
          Not enough data to backtest yet. A biomarker series needs at least{" "}
          {result.min_series_points} post-treatment measurements. Add
          measurements under{" "}
          <Link href="/tracking" className="text-teal-700 underline">
            Patients
          </Link>{" "}
          or load the demo cohort.
        </p>
      )}

      {!loading && result && result.n_points > 0 && overall && (
        <>
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard
              label="95% coverage"
              value={fmtPct(overall.coverage_95)}
              sub={coverageSub}
              tone={coverageTone(overall.coverage_95)}
            />
            <MetricCard
              label="MAE"
              value={fmtNum(overall.mae_pct)}
              sub="mean abs error (% of baseline)"
            />
            <MetricCard
              label="RMSE"
              value={fmtNum(overall.rmse_pct)}
              sub="root-mean-square error"
            />
            <MetricCard
              label="Bias"
              value={
                overall.bias_pct === null
                  ? "—"
                  : `${overall.bias_pct > 0 ? "+" : ""}${overall.bias_pct.toFixed(1)}%`
              }
              sub="mean signed error"
              tone={
                overall.bias_pct !== null && Math.abs(overall.bias_pct) > 5
                  ? "text-amber-600"
                  : "text-slate-800"
              }
            />
            <MetricCard
              label="Held-out points"
              value={String(result.n_points)}
              sub={`${result.n_series} series · ${result.n_patients} patient${
                result.n_patients === 1 ? "" : "s"
              }`}
            />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <h2 className="font-medium text-slate-800">
                Predicted vs. observed
              </h2>
              <span className="text-xs text-slate-500">
                each point = one held-out measurement · dashed line = perfect
                prediction
              </span>
            </div>
            <DiagnosticsScatter points={result.points} />
            <p className="mt-2 text-xs text-slate-500">
              Change is expressed as a percent of each series&apos; fitted
              baseline so biomarkers on different scales share one axis. Teal
              points fell inside the model&apos;s 95% predictive band; amber
              points fell outside it.
            </p>
          </section>

          <GroupTable title="By peptide" rows={result.by_peptide} />
          <GroupTable title="By biomarker" rows={result.by_biomarker} />

          <p className="text-xs text-slate-500">
            Method: {result.method} backtest over the {result.reference_path}{" "}
            reference path. Coverage near 95% means the credible bands are
            honest; well below means the model is over-confident, well above
            means it is over-hedged. This is an internal performance monitor,
            not a clinical validation.
          </p>
        </>
      )}
    </div>
  );
}
