"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  CohortTrajectoryChart,
  DoseResponseChart,
} from "../components/CohortChart";
import {
  getBiomarkerCatalog,
  getCohort,
  listPeptidesWithData,
} from "../lib/api";
import type {
  BiomarkerCatalogEntry,
  CohortPeptideSummary,
  CohortResult,
} from "../lib/types";

export default function CohortPage() {
  const [peptides, setPeptides] = useState<CohortPeptideSummary[]>([]);
  const [peptide, setPeptide] = useState<string>("");
  const [catalog, setCatalog] = useState<BiomarkerCatalogEntry[]>([]);
  const [biomarker, setBiomarker] = useState<string>("");
  const [result, setResult] = useState<CohortResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listPeptidesWithData()
      .then((ps) => {
        setPeptides(ps);
        if (ps.length > 0) setPeptide(ps[0].peptide_name);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!peptide) return;
    setBiomarker("");
    setResult(null);
    getBiomarkerCatalog(peptide)
      .then((c) => {
        setCatalog(c);
        const first = c.find((m) => m.n_observed > 0) || c[0];
        if (first) setBiomarker(first.name);
      })
      .catch((e) => setError(e.message));
  }, [peptide]);

  useEffect(() => {
    if (!peptide || !biomarker) return;
    setLoading(true);
    getCohort({ peptide, biomarker })
      .then((r) => {
        setResult(r);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [peptide, biomarker]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Cohort analysis</h1>
          <p className="text-sm text-slate-600">
            Cross-patient trends time-aligned to treatment start. Shaded band shows
            the expected response window from the peptide&apos;s biomarker panel.
          </p>
        </div>
        <Link href="/tracking" className="text-sm text-teal-700 underline">
          ← Patients
        </Link>
      </header>

      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm">
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">Peptide</span>
          <select
            value={peptide}
            onChange={(e) => setPeptide(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
            disabled={peptides.length === 0}
          >
            {peptides.length === 0 && <option>—</option>}
            {peptides.map((p) => (
              <option key={p.peptide_name} value={p.peptide_name}>
                {p.peptide_name} ({p.n_patients}p · {p.n_measurements}m)
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">Biomarker</span>
          <select
            value={biomarker}
            onChange={(e) => setBiomarker(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          >
            {catalog.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} {c.n_observed > 0 ? `· ${c.n_observed}m` : "(no data)"}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {peptides.length === 0 && !error && (
        <p className="text-sm text-slate-500">
          No treatments recorded yet. Add a patient + treatment first under{" "}
          <Link href="/tracking" className="text-teal-700 underline">
            Patients
          </Link>
          .
        </p>
      )}

      {loading && <p className="text-sm text-slate-500">Loading cohort…</p>}

      {result && (
        <>
          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-2 flex items-baseline justify-between">
              <h2 className="font-medium text-slate-800">
                {result.peptide} → {result.biomarker_name}
              </h2>
              <span className="text-xs text-slate-500">
                {result.n_patients} patient{result.n_patients === 1 ? "" : "s"} ·{" "}
                {result.n_measurements} measurement
                {result.n_measurements === 1 ? "" : "s"}
                {result.expected ? ` · expected ${result.expected.direction}` : ""}
              </span>
            </div>
            <CohortTrajectoryChart result={result} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-2 font-medium text-slate-800">Dose-response</h2>
            <DoseResponseChart result={result} />
            {result.dose_response.length > 0 && (
              <table className="mt-3 w-full text-xs text-slate-700">
                <thead className="text-left text-slate-500">
                  <tr>
                    <th className="py-1">Dose</th>
                    <th>n patients</th>
                    <th>n measurements</th>
                    <th>Median</th>
                    <th>Δ vs baseline</th>
                  </tr>
                </thead>
                <tbody>
                  {result.dose_response.map((d) => (
                    <tr key={`${d.dose}-${d.dose_unit}`} className="border-t border-slate-100">
                      <td className="py-1">
                        {d.dose} {d.dose_unit}
                      </td>
                      <td>{d.n_patients}</td>
                      <td>{d.n_measurements}</td>
                      <td>{d.median_value}</td>
                      <td>
                        {d.pct_change_from_baseline === null
                          ? "—"
                          : `${d.pct_change_from_baseline}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
