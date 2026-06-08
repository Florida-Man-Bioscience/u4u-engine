"use client";

import { useMemo, useState } from "react";
import type {
  RegulatoryCategorySlug,
  RegulatoryPeptide,
  RegulatoryPeptidesPayload,
} from "../../lib/types";
import { PeptideCard } from "./PeptideCard";

type Filter = "all" | RegulatoryCategorySlug;

const FILTER_ORDER: Array<{ key: Filter; label: string }> = [
  { key: "all", label: "All" },
  { key: "cat1", label: "Category 1" },
  { key: "cat2", label: "Category 2" },
  { key: "removed_from_cat2", label: "Removed from Cat. 2" },
  { key: "pcac_review", label: "PCAC Review" },
  { key: "unscheduled", label: "Unscheduled" },
];

export function PeptideGrid({ payload }: { payload: RegulatoryPeptidesPayload }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const visible = useMemo<RegulatoryPeptide[]>(() => {
    const q = query.trim().toLowerCase();
    return payload.peptides.filter((p) => {
      if (filter !== "all" && p.category !== filter) return false;
      if (!q) return true;
      const hay = [p.name, ...p.aliases].join(" ").toLowerCase();
      return hay.includes(q);
    });
  }, [payload.peptides, filter, query]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {FILTER_ORDER.map((f) => {
          const count =
            f.key === "all"
              ? payload.peptides.length
              : payload.stats.by_category[f.key] ?? 0;
          const active = filter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                active
                  ? "border-blue-500/60 bg-blue-500/15 text-blue-200"
                  : "border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200"
              }`}
            >
              {f.label}
              <span className="ml-1.5 text-[10px] opacity-70">{count}</span>
            </button>
          );
        })}
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search peptide or alias…"
          className="ml-auto w-full max-w-xs rounded-md border border-zinc-700 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-100 placeholder:text-zinc-500 focus:border-blue-500 focus:outline-none sm:w-auto"
        />
      </div>

      {visible.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
          No peptides match the current filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((p) => (
            <PeptideCard
              key={p.slug}
              peptide={p}
              category={payload.categories[p.category]}
            />
          ))}
        </div>
      )}
    </div>
  );
}
