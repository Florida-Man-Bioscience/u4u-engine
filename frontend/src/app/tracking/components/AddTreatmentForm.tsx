"use client";

import { useState } from "react";
import { createTreatment } from "../lib/api";
import type { Treatment } from "../lib/types";

const KNOWN_PEPTIDES = [
  "BPC-157",
  "TB-500",
  "Thymosin Beta-4",
  "GHK-Cu",
  "MOTS-c",
  "CJC-1295",
  "Ipamorelin",
  "GHRP-2",
  "MGF",
  "AOD-9604",
  "Thymosin Alpha-1",
  "Epitalon",
  "Selank",
  "Semax",
  "DSIP",
  "Dihexa",
  "Kisspeptin",
  "Melanotan II",
  "LL-37",
  "KPV",
];

export function AddTreatmentForm({
  patientId,
  onCreated,
}: {
  patientId: string;
  onCreated: (t: Treatment) => void;
}) {
  const [peptide, setPeptide] = useState(KNOWN_PEPTIDES[0]);
  const [startDate, setStartDate] = useState("");
  const [dose, setDose] = useState("");
  const [doseUnit, setDoseUnit] = useState("mg");
  const [schedule, setSchedule] = useState("");
  const [route, setRoute] = useState("SC");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!startDate) {
      setError("start date required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const t = await createTreatment(patientId, {
        peptide_name: peptide,
        start_date: startDate,
        end_date: null,
        dose: dose ? Number(dose) : null,
        dose_unit: dose ? doseUnit : null,
        schedule: schedule || null,
        route: route || null,
        notes: null,
      });
      onCreated(t);
      setDose("");
      setSchedule("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="grid grid-cols-2 gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm md:grid-cols-7"
    >
      <label className="col-span-2 flex flex-col">
        <span className="text-xs text-slate-500">Peptide</span>
        <select
          value={peptide}
          onChange={(e) => setPeptide(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        >
          {KNOWN_PEPTIDES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Start date</span>
        <input
          type="date"
          required
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        />
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Dose</span>
        <input
          type="number"
          step="any"
          value={dose}
          onChange={(e) => setDose(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        />
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Unit</span>
        <select
          value={doseUnit}
          onChange={(e) => setDoseUnit(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        >
          <option>mg</option>
          <option>mcg</option>
          <option>IU</option>
          <option>mL</option>
        </select>
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Schedule</span>
        <input
          value={schedule}
          onChange={(e) => setSchedule(e.target.value)}
          placeholder="e.g. 2x/week"
          className="rounded border border-slate-300 px-2 py-1"
        />
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Route</span>
        <select
          value={route}
          onChange={(e) => setRoute(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        >
          <option>SC</option>
          <option>IM</option>
          <option>PO</option>
          <option>topical</option>
          <option>IV</option>
        </select>
      </label>
      <div className="col-span-2 flex items-end gap-2 md:col-span-7">
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-teal-700 px-3 py-1.5 text-white hover:bg-teal-800 disabled:opacity-50"
        >
          {busy ? "Saving…" : "Add treatment"}
        </button>
        {error && <span className="text-red-600">{error}</span>}
      </div>
    </form>
  );
}
