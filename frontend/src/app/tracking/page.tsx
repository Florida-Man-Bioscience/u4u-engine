"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AddPatientForm } from "./components/AddPatientForm";
import { deletePatient, listPatients, seedDemoData } from "./lib/api";
import type { Patient } from "./lib/types";

export default function TrackingHome() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      setPatients(await listPatients());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function loadDemoData() {
    const hasData = patients.length > 0;
    if (
      hasData &&
      !confirm(
        `Reset and reload demo data? This will delete ${patients.length} existing patient(s) and reseed.`,
      )
    ) {
      return;
    }
    setSeeding(true);
    setSeedMessage(null);
    setError(null);
    try {
      const result = await seedDemoData({ force: hasData });
      if (result.skipped) {
        setSeedMessage(
          `Tracking DB already has ${result.skipped} patient(s) — no changes made.`,
        );
      } else {
        setSeedMessage(
          `Loaded ${result.patients} patient(s), ${result.treatments} treatment(s), ${result.measurements} measurement(s).`,
        );
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to seed");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Biomarker tracking</h1>
          <p className="text-sm text-slate-600">
            Track patient measurements over time on peptide therapy. View per-patient
            longitudinal charts or jump to{" "}
            <Link href="/tracking/cohort" className="text-teal-700 underline">
              cross-patient cohort analysis
            </Link>
            .
          </p>
        </div>
        <button
          type="button"
          onClick={loadDemoData}
          disabled={seeding}
          className="whitespace-nowrap rounded border border-teal-700 bg-white px-3 py-1.5 text-sm text-teal-700 hover:bg-teal-50 disabled:opacity-50"
        >
          {seeding
            ? "Loading…"
            : patients.length > 0
              ? "Reload demo data"
              : "Load demo data"}
        </button>
      </header>

      {seedMessage && (
        <p className="rounded border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-800">
          {seedMessage}
        </p>
      )}

      <AddPatientForm onCreated={(p) => setPatients((xs) => [p, ...xs])} />

      {error && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <section>
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-500">
          Patients ({patients.length})
        </h2>
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : patients.length === 0 ? (
          <p className="text-sm text-slate-500">
            No patients yet. Add one above to begin tracking.
          </p>
        ) : (
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
            {patients.map((p) => (
              <li key={p.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <Link
                  href={`/tracking/patients/${p.id}`}
                  className="flex-1 hover:bg-slate-50"
                >
                  <span className="font-medium text-slate-800">{p.label}</span>
                  <span className="ml-3 text-slate-500">
                    {[p.sex, p.birth_year].filter(Boolean).join(" · ") || "—"}
                  </span>
                </Link>
                <button
                  onClick={async () => {
                    if (!confirm(`Delete ${p.label}? This removes treatments and measurements.`)) return;
                    await deletePatient(p.id);
                    refresh();
                  }}
                  className="text-xs text-red-600 hover:underline"
                >
                  delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
