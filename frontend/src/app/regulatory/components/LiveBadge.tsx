import type { LiveSourceStatus } from "../../lib/types";

const COPY: Record<LiveSourceStatus, { label: string; cls: string }> = {
  fresh: { label: "Live", cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  stale: { label: "Stale", cls: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  unavailable: { label: "Offline", cls: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30" },
};

export function LiveBadge({
  status,
  fetchedAt,
}: {
  status: LiveSourceStatus;
  fetchedAt: number | null;
}) {
  const { label, cls } = COPY[status];
  const when =
    fetchedAt != null
      ? new Date(fetchedAt * 1000).toLocaleString(undefined, {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })
      : null;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${cls}`}
      title={when ? `Last fetched ${when}` : undefined}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
      {when && status !== "unavailable" ? (
        <span className="text-[10px] opacity-70">· {when}</span>
      ) : null}
    </span>
  );
}
