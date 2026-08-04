import type { LiveSourceStatus } from "@/app/lib/types";

const COPY: Record<LiveSourceStatus, { label: string; cls: string }> = {
  fresh: { label: "Live", cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  stale: { label: "Stale", cls: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  unavailable: { label: "Offline", cls: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30" },
};

const SUBTLE_DOT: Record<LiveSourceStatus, string> = {
  fresh: "bg-emerald-400/50",
  stale: "bg-amber-400/50",
  unavailable: "bg-zinc-500/40",
};

function formatWhen(fetchedAt: number | null): string | null {
  if (fetchedAt == null) return null;
  return new Date(fetchedAt * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function LiveBadge({
  status,
  fetchedAt,
  variant = "pill",
}: {
  status: LiveSourceStatus;
  fetchedAt: number | null;
  variant?: "pill" | "subtle";
}) {
  const when = formatWhen(fetchedAt);

  if (variant === "subtle") {
    return (
      <span
        className="mt-1 inline-flex items-center gap-1 text-[9px] text-zinc-500"
        title={
          when
            ? `${status === "fresh" ? "Updated" : status === "stale" ? "Stale, last update" : "No data, last attempt"} ${when}`
            : `Status: ${status}`
        }
      >
        <span className={`h-1 w-1 rounded-full ${SUBTLE_DOT[status]}`} />
        {when && status !== "unavailable" ? when : status}
      </span>
    );
  }

  const { label, cls } = COPY[status];
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
