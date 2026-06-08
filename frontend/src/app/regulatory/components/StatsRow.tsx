import type { RegulatoryPeptidesPayload } from "../../lib/types";

export function StatsRow({ payload }: { payload: RegulatoryPeptidesPayload }) {
  const cells: Array<{ label: string; value: number; tone: string }> = [
    {
      label: "Category 1 (Legal)",
      value: payload.stats.by_category.cat1 ?? 0,
      tone: "text-emerald-300",
    },
    {
      label: "Category 2 (Prohibited)",
      value: payload.stats.by_category.cat2 ?? 0,
      tone: "text-red-300",
    },
    {
      label: "Removed from Cat. 2",
      value: payload.stats.by_category.removed_from_cat2 ?? 0,
      tone: "text-purple-300",
    },
    {
      label: "PCAC July 2026",
      value: payload.stats.by_pcac_wave.july_2026 ?? 0,
      tone: "text-amber-300",
    },
    {
      label: "PCAC Early 2027",
      value: payload.stats.by_pcac_wave.early_2027 ?? 0,
      tone: "text-amber-300",
    },
    {
      label: "Total Tracked",
      value: payload.stats.total_peptides,
      tone: "text-zinc-200",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cells.map((c) => (
        <div
          key={c.label}
          className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3"
        >
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">
            {c.label}
          </div>
          <div className={`mt-1 text-2xl font-bold ${c.tone}`}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}
