import type { RegulatoryEvent } from "@/app/lib/types";

const KIND_DOT: Record<RegulatoryEvent["kind"], string> = {
  category_change: "bg-purple-400",
  policy: "bg-blue-400",
  pcac: "bg-amber-400",
  deadline: "bg-red-400",
  rulemaking: "bg-emerald-400",
};

export function EventTimeline({ events }: { events: RegulatoryEvent[] }) {
  const sorted = [...events].sort((a, b) => a.date.localeCompare(b.date));
  return (
    <ol className="relative border-l border-zinc-800 pl-6">
      {sorted.map((e) => (
        <li key={`${e.date}-${e.title}`} className="mb-6 last:mb-0">
          <span
            className={`absolute -left-[6px] mt-1.5 h-3 w-3 rounded-full ring-4 ring-[#0d0f14] ${KIND_DOT[e.kind]}`}
          />
          <div className="font-mono text-[11px] uppercase tracking-wide text-zinc-500">
            {e.date}
          </div>
          <div className="mt-0.5 text-sm font-semibold text-zinc-100">{e.title}</div>
          <p className="mt-1 text-xs text-zinc-400">{e.impact}</p>
          <a
            href={e.source_url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-block text-[11px] text-blue-400 hover:underline"
          >
            {e.source_label} →
          </a>
        </li>
      ))}
    </ol>
  );
}
