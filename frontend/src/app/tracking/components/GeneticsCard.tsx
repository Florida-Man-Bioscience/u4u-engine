"use client";

import { useEffect, useMemo, useState } from "react";
import { getGenetics, getPriors, regenerateGenetics } from "../lib/api";
import type {
  GeneticPrior,
  GeneticsResponse,
  GeneticVariant,
} from "../lib/types";

interface Props {
  patientId: string;
  /** Filter the priors list to peptides on this patient's treatments. */
  treatmentPeptides: string[];
}

function fmtPct(x: number): string {
  const sign = x >= 0 ? "+" : "";
  return `${sign}${(x * 100).toFixed(1)}%`;
}

export function GeneticsCard({ patientId, treatmentPeptides }: Props) {
  const [genetics, setGenetics] = useState<GeneticsResponse | null>(null);
  const [priors, setPriors] = useState<GeneticPrior[]>([]);
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      const [g, p] = await Promise.all([
        getGenetics(patientId),
        getPriors(patientId),
      ]);
      setGenetics(g);
      setPriors(p.priors);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to load genetics");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  async function regenerate() {
    setBusy(true);
    setError(null);
    try {
      await regenerateGenetics(patientId);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setBusy(false);
    }
  }

  const variants = genetics?.profile?.variants ?? [];
  const treatmentSet = useMemo(
    () => new Set(treatmentPeptides),
    [treatmentPeptides],
  );
  const filteredPriors = useMemo(
    () =>
      priors
        .filter((p) => treatmentSet.has(p.peptide) || p.n_relevant_variants > 0)
        .sort((a, b) => {
          const aOn = treatmentSet.has(a.peptide) ? 1 : 0;
          const bOn = treatmentSet.has(b.peptide) ? 1 : 0;
          if (aOn !== bOn) return bOn - aOn;
          return Math.abs(b.mean_pct_change) - Math.abs(a.mean_pct_change);
        }),
    [priors, treatmentSet],
  );

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <h3 className="font-medium text-slate-800">Genetic profile</h3>
          <p className="text-xs text-slate-500">
            {genetics?.profile
              ? `${variants.length} catalog variants · source: ${genetics.source}`
              : "no profile yet"}
          </p>
        </div>
        <button
          onClick={regenerate}
          disabled={busy}
          className="rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          {busy ? "Generating…" : genetics?.profile ? "Regenerate" : "Generate"}
        </button>
      </div>
      {error && (
        <p className="mb-2 rounded border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-700">
          {error}
        </p>
      )}

      {filteredPriors.length > 0 && (
        <div className="mb-3">
          <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">
            Per-peptide priors{" "}
            <span className="text-slate-400">(mean ± 1σ)</span>
          </div>
          <ul className="divide-y divide-slate-100 rounded border border-slate-200 text-sm">
            {filteredPriors.slice(0, 8).map((p) => {
              const onTx = treatmentSet.has(p.peptide);
              const positive = p.mean_pct_change >= 0;
              return (
                <li
                  key={p.peptide}
                  className="flex items-center justify-between px-3 py-1.5"
                >
                  <span className={onTx ? "font-medium text-slate-800" : "text-slate-700"}>
                    {p.peptide}
                    {onTx && (
                      <span className="ml-2 rounded bg-teal-50 px-1.5 py-0.5 text-xs text-teal-700">
                        on therapy
                      </span>
                    )}
                  </span>
                  <span className="text-xs">
                    <span
                      className={
                        positive ? "font-mono text-teal-700" : "font-mono text-rose-700"
                      }
                    >
                      {fmtPct(p.mean_pct_change)}
                    </span>
                    <span className="ml-1 font-mono text-slate-400">
                      ±{(p.sd_pct_change * 100).toFixed(1)}%
                    </span>
                    <span className="ml-2 text-slate-400">
                      {p.n_relevant_variants}v
                    </span>
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {variants.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded((x) => !x)}
            className="text-xs text-teal-700 underline"
          >
            {expanded ? "Hide variants" : `Show all ${variants.length} variants`}
          </button>
          {expanded && (
            <table className="mt-2 w-full text-xs text-slate-700">
              <thead className="text-left text-slate-500">
                <tr>
                  <th className="py-1">rsID</th>
                  <th>Gene</th>
                  <th>Genotype</th>
                  <th>Dosage</th>
                </tr>
              </thead>
              <tbody>
                {variants.map((v: GeneticVariant) => (
                  <tr key={v.rsid} className="border-t border-slate-100">
                    <td className="py-1 font-mono">{v.rsid}</td>
                    <td>{v.gene}</td>
                    <td>{v.genotype}</td>
                    <td>{v.dosage}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
