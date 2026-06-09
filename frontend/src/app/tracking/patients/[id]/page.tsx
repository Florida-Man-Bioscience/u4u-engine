"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useMemo, useState } from "react";
import { AddMeasurementForm } from "../../components/AddMeasurementForm";
import { AddTreatmentForm } from "../../components/AddTreatmentForm";
import { BiomarkerLineChart } from "../../components/BiomarkerLineChart";
import {
  getBiomarkerCatalog,
  getPatient,
  listMeasurements,
  listTreatments,
} from "../../lib/api";
import type {
  BiomarkerCatalogEntry,
  Measurement,
  Patient,
  Treatment,
} from "../../lib/types";

export default function PatientDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [catalog, setCatalog] = useState<BiomarkerCatalogEntry[]>([]);
  const [activeTreatmentId, setActiveTreatmentId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [p, ts, ms] = await Promise.all([
        getPatient(id),
        listTreatments(id),
        listMeasurements(id),
      ]);
      setPatient(p);
      setTreatments(ts);
      setMeasurements(ms);
      if (ts.length > 0) {
        setActiveTreatmentId((curr) => curr || ts[0].id);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Load the biomarker catalog whenever the active treatment changes.
  const activeTreatment = treatments.find((t) => t.id === activeTreatmentId);
  useEffect(() => {
    if (!activeTreatment) {
      setCatalog([]);
      return;
    }
    getBiomarkerCatalog(activeTreatment.peptide_name)
      .then(setCatalog)
      .catch((e) => setError(e.message));
  }, [activeTreatment]);

  // Group measurements by biomarker.
  const grouped = useMemo(() => {
    const map = new Map<string, Measurement[]>();
    for (const m of measurements) {
      if (!map.has(m.biomarker_name)) map.set(m.biomarker_name, []);
      map.get(m.biomarker_name)!.push(m);
    }
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [measurements]);

  if (error) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
        <Link href="/tracking" className="mt-3 inline-block text-sm text-teal-700 underline">
          ← Back to patients
        </Link>
      </div>
    );
  }

  if (!patient) {
    return <div className="p-6 text-sm text-slate-500">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header>
        <Link href="/tracking" className="text-sm text-teal-700 underline">
          ← Patients
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Patient {patient.label}</h1>
        <p className="text-sm text-slate-600">
          {[patient.sex, patient.birth_year && `b. ${patient.birth_year}`]
            .filter(Boolean)
            .join(" · ") || "—"}
        </p>
      </header>

      <section>
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-500">
          Treatments
        </h2>
        <AddTreatmentForm
          patientId={id}
          onCreated={(t) => {
            setTreatments((xs) => [t, ...xs]);
            setActiveTreatmentId(t.id);
          }}
        />
        {treatments.length > 0 && (
          <ul className="mt-3 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white text-sm">
            {treatments.map((t) => (
              <li
                key={t.id}
                onClick={() => setActiveTreatmentId(t.id)}
                className={`flex cursor-pointer items-center justify-between px-4 py-2 ${
                  t.id === activeTreatmentId ? "bg-teal-50" : "hover:bg-slate-50"
                }`}
              >
                <span>
                  <span className="font-medium">{t.peptide_name}</span>
                  <span className="ml-2 text-slate-500">
                    {t.dose ?? "?"} {t.dose_unit ?? ""} · {t.schedule ?? "—"} · {t.route ?? "—"}
                  </span>
                </span>
                <span className="text-xs text-slate-500">start {t.start_date}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-500">
          Add measurement
        </h2>
        {catalog.length > 0 ? (
          <AddMeasurementForm
            patientId={id}
            treatments={treatments}
            catalog={catalog}
            onCreated={() => refresh()}
          />
        ) : (
          <p className="text-sm text-slate-500">
            Add a treatment above to see its biomarker panel.
          </p>
        )}
      </section>

      <section className="space-y-6">
        <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
          Longitudinal charts ({grouped.length})
        </h2>
        {grouped.length === 0 && (
          <p className="text-sm text-slate-500">No measurements yet.</p>
        )}
        {grouped.map(([name, rows]) => {
          const expected = catalog.find((c) => c.name === name) ?? null;
          const start = activeTreatment?.start_date ?? null;
          return (
            <div key={name} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-2 flex items-baseline justify-between">
                <h3 className="font-medium text-slate-800">{name}</h3>
                <span className="text-xs text-slate-500">
                  {rows.length} measurement{rows.length === 1 ? "" : "s"}
                  {expected ? ` · expected ${expected.direction}` : ""}
                </span>
              </div>
              <BiomarkerLineChart
                measurements={rows}
                expected={expected}
                treatmentStartIso={start}
              />
            </div>
          );
        })}
      </section>
    </div>
  );
}
