"use client";

import { useState } from "react";
import { createPatient } from "../lib/api";
import type { Patient } from "../lib/types";

export function AddPatientForm({ onCreated }: { onCreated: (p: Patient) => void }) {
  const [label, setLabel] = useState("");
  const [sex, setSex] = useState("");
  const [birthYear, setBirthYear] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!label.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const p = await createPatient({
        label: label.trim(),
        sex: sex || null,
        birth_year: birthYear ? Number(birthYear) : null,
      });
      onCreated(p);
      setLabel("");
      setSex("");
      setBirthYear("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-wrap items-end gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm"
    >
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Label</span>
        <input
          required
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="P-001"
          className="rounded border border-slate-300 px-2 py-1"
        />
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Sex</span>
        <select
          value={sex}
          onChange={(e) => setSex(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1"
        >
          <option value="">—</option>
          <option value="M">M</option>
          <option value="F">F</option>
          <option value="other">other</option>
        </select>
      </label>
      <label className="flex flex-col">
        <span className="text-xs text-slate-500">Birth year</span>
        <input
          type="number"
          value={birthYear}
          onChange={(e) => setBirthYear(e.target.value)}
          placeholder="1990"
          className="w-24 rounded border border-slate-300 px-2 py-1"
        />
      </label>
      <button
        type="submit"
        disabled={busy}
        className="rounded bg-teal-700 px-3 py-1.5 text-white hover:bg-teal-800 disabled:opacity-50"
      >
        {busy ? "Saving…" : "Add patient"}
      </button>
      {error && <span className="text-red-600">{error}</span>}
    </form>
  );
}
