import type {
  RegulatoryCategory,
  RegulatoryCategorySlug,
  RegulatoryPeptide,
} from "../../lib/types";
import { LiveBadge } from "./LiveBadge";

const CATEGORY_RING: Record<RegulatoryCategorySlug, string> = {
  cat1: "border-emerald-500/40 bg-emerald-500/5",
  cat2: "border-red-500/40 bg-red-500/5",
  removed_from_cat2: "border-purple-500/40 bg-purple-500/5",
  pcac_review: "border-amber-500/40 bg-amber-500/5",
  unscheduled: "border-zinc-500/30 bg-zinc-500/5",
};

const CATEGORY_BADGE: Record<RegulatoryCategorySlug, string> = {
  cat1: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  cat2: "bg-red-500/15 text-red-300 border-red-500/30",
  removed_from_cat2: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  pcac_review: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  unscheduled: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

export function PeptideCard({
  peptide,
  category,
}: {
  peptide: RegulatoryPeptide;
  category: RegulatoryCategory;
}) {
  const trials = peptide.live?.clinicaltrials;
  const openfda = peptide.live?.openfda;
  const fr = peptide.live?.federal_register;

  return (
    <article
      className={`flex flex-col gap-3 rounded-lg border p-4 ${CATEGORY_RING[peptide.category]}`}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-white">{peptide.name}</h3>
          {peptide.aliases.length > 0 && (
            <p className="mt-0.5 truncate text-xs text-zinc-400">
              {peptide.aliases.join(" · ")}
            </p>
          )}
        </div>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${CATEGORY_BADGE[peptide.category]}`}
          title={category.description}
        >
          {category.label.split(" — ")[0]}
        </span>
      </header>

      {peptide.engine_covered && (
        <p className="rounded border border-[#1a6b4a]/40 bg-[#1a6b4a]/10 px-2 py-1 text-[11px] text-emerald-300">
          ✦ Engine scores this peptide
        </p>
      )}

      {peptide.medspa_uses.length > 0 && (
        <div className="text-xs text-zinc-400">
          <p className="mb-1 font-medium text-zinc-300">Medspa uses</p>
          <ul className="list-disc pl-4">
            {peptide.medspa_uses.slice(0, 3).map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
        </div>
      )}

      <dl className="grid grid-cols-3 gap-2 border-t border-zinc-800 pt-3 text-[11px]">
        <div>
          <dt className="text-zinc-500">Active trials</dt>
          <dd className="mt-0.5 text-sm font-semibold text-zinc-100">
            {trials?.data?.active_trials ?? "—"}
            {trials?.data?.total_trials != null && (
              <span className="ml-1 text-[10px] font-normal text-zinc-500">
                / {trials.data.total_trials}
              </span>
            )}
          </dd>
          {trials && (
            <LiveBadge status={trials.status} fetchedAt={trials.fetched_at} />
          )}
        </div>
        <div>
          <dt className="text-zinc-500">openFDA recalls</dt>
          <dd className="mt-0.5 text-sm font-semibold text-zinc-100">
            {openfda?.data?.recalls_total ?? "—"}
          </dd>
          {openfda && (
            <LiveBadge status={openfda.status} fetchedAt={openfda.fetched_at} />
          )}
        </div>
        <div>
          <dt className="text-zinc-500">Fed. Register</dt>
          <dd className="mt-0.5 text-sm font-semibold text-zinc-100">
            {fr?.data?.total ?? "—"}
          </dd>
          {fr && <LiveBadge status={fr.status} fetchedAt={fr.fetched_at} />}
        </div>
      </dl>

      {peptide.history.length > 0 && (
        <details className="text-[11px] text-zinc-400">
          <summary className="cursor-pointer text-zinc-300 hover:text-white">
            Regulatory history ({peptide.history.length})
          </summary>
          <ol className="mt-2 space-y-1.5 border-l border-zinc-700 pl-3">
            {peptide.history.map((h) => (
              <li key={`${h.date}-${h.note}`}>
                <div className="font-mono text-[10px] text-zinc-500">{h.date}</div>
                <div>{h.note}</div>
              </li>
            ))}
          </ol>
        </details>
      )}

      {fr?.data?.documents && fr.data.documents.length > 0 && (
        <details className="text-[11px] text-zinc-400">
          <summary className="cursor-pointer text-zinc-300 hover:text-white">
            Recent Federal Register notices
          </summary>
          <ul className="mt-2 space-y-1">
            {fr.data.documents.map((d) => (
              <li key={d.document_number ?? d.title ?? ""}>
                <a
                  href={d.url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 hover:underline"
                >
                  {d.title ?? "(untitled)"}
                </a>
                <span className="ml-1 text-zinc-500">· {d.publication_date}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}
