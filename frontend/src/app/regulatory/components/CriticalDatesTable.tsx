import type { RegulatoryEvent } from "../../lib/types";

const STATUS_PILL: Record<RegulatoryEvent["status"], string> = {
  past: "bg-zinc-700/40 text-zinc-300 border-zinc-600/40",
  upcoming: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  tbd: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
};

function daysUntil(dateStr: string): number {
  const target = new Date(`${dateStr}T00:00:00Z`).getTime();
  const now = Date.now();
  return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
}

export function CriticalDatesTable({ events }: { events: RegulatoryEvent[] }) {
  const sorted = [...events].sort((a, b) => a.date.localeCompare(b.date));
  return (
    <div className="overflow-hidden rounded-lg border border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-900/60 text-xs uppercase tracking-wide text-zinc-400">
          <tr>
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2">Event</th>
            <th className="px-3 py-2">Impact</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e) => {
            const days = daysUntil(e.date);
            const isCritical = e.status === "upcoming" && days >= 0 && days <= 30;
            return (
              <tr
                key={`${e.date}-${e.title}`}
                className="border-t border-zinc-800/60 align-top"
              >
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs text-zinc-300">
                  {e.date}
                </td>
                <td className="px-3 py-2">
                  <div className="text-zinc-100">{e.title}</div>
                  <a
                    href={e.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-blue-400 hover:underline"
                  >
                    {e.source_label}
                  </a>
                </td>
                <td className="px-3 py-2 text-xs text-zinc-400">{e.impact}</td>
                <td className="whitespace-nowrap px-3 py-2">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${STATUS_PILL[e.status]}`}
                  >
                    {isCritical
                      ? `⚡ ${days}d`
                      : e.status === "upcoming"
                        ? `${days}d`
                        : e.status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
