"use client";

import { useState } from "react";
import { createMeasurement, uploadMeasurementCsv } from "../lib/api";
import type {
  BiomarkerCatalogEntry,
  Measurement,
  Treatment,
} from "../lib/types";

export function AddMeasurementForm({
  patientId,
  treatments,
  catalog,
  onCreated,
}: {
  patientId: string;
  treatments: Treatment[];
  catalog: BiomarkerCatalogEntry[];
  onCreated: (m: Measurement) => void;
}) {
  const [biomarker, setBiomarker] = useState<string>(catalog[0]?.name ?? "");
  const [value, setValue] = useState("");
  const [measuredAt, setMeasuredAt] = useState("");
  const [treatmentId, setTreatmentId] = useState<string>(treatments[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const entry = catalog.find((c) => c.name === biomarker);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!biomarker || !measuredAt || value === "") {
      setError("biomarker, value, and date are required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const m = await createMeasurement({
        patient_id: patientId,
        biomarker_name: biomarker,
        value: Number(value),
        measured_at: measuredAt,
        treatment_id: treatmentId || null,
        modality: entry?.modality ?? null,
        unit: entry?.unit ?? null,
      });
      onCreated(m);
      setValue("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleCsv(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const res = await uploadMeasurementCsv(file);
      if (res.errors?.length) {
        setError(`Imported ${res.created}; ${res.errors.length} row error(s)`);
      }
      // Trigger a parent reload by re-emitting a synthetic measurement
      // (the parent re-fetches anyway on onCreated callback).
      onCreated({
        id: "_bulk",
        patient_id: patientId,
        treatment_id: null,
        biomarker_name: "",
        modality: null,
        value: 0,
        unit: null,
        measured_at: new Date().toISOString(),
        notes: null,
        created_at: new Date().toISOString(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "csv failed");
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
      <form onSubmit={submit} className="grid grid-cols-2 gap-2 md:grid-cols-6">
        <label className="col-span-2 flex flex-col">
          <span className="text-xs text-slate-500">Biomarker</span>
          <select
            value={biomarker}
            onChange={(e) => setBiomarker(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          >
            {catalog.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.modality})
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">Value</span>
          <input
            required
            type="number"
            step="any"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">
            Unit {entry ? `(${entry.unit})` : ""}
          </span>
          <input
            value={entry?.unit ?? ""}
            readOnly
            className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">Measured at</span>
          <input
            required
            type="date"
            value={measuredAt}
            onChange={(e) => setMeasuredAt(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-slate-500">Treatment</span>
          <select
            value={treatmentId}
            onChange={(e) => setTreatmentId(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          >
            <option value="">— none —</option>
            {treatments.map((t) => (
              <option key={t.id} value={t.id}>
                {t.peptide_name} (start {t.start_date})
              </option>
            ))}
          </select>
        </label>
        <div className="col-span-2 flex items-end gap-3 md:col-span-6">
          <button
            type="submit"
            disabled={busy}
            className="rounded bg-teal-700 px-3 py-1.5 text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {busy ? "Saving…" : "Add measurement"}
          </button>
          <label className="cursor-pointer text-xs text-slate-600 underline">
            Or upload CSV
            <input
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={handleCsv}
            />
          </label>
          {error && <span className="text-red-600">{error}</span>}
        </div>
      </form>
      {entry && (
        <p className="mt-2 text-xs text-slate-500">
          Expected {entry.direction}
          {entry.timeframe_weeks_min !== null || entry.timeframe_weeks_max !== null
            ? ` over ${entry.timeframe_weeks_min ?? "?"}–${
                entry.timeframe_weeks_max ?? "?"
              } wk`
            : ""}{" "}
          ({entry.purpose}).
          {entry.effect_size && <> · {entry.effect_size}</>}
        </p>
      )}
    </div>
  );
}
