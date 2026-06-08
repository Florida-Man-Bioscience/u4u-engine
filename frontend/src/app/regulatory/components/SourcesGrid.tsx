import type {
  DocketLiveSummary,
  LiveEnvelope,
  RegulatorySource,
} from "../../lib/types";
import { LiveBadge } from "./LiveBadge";

export function SourcesGrid({
  sources,
  docketLive,
}: {
  sources: RegulatorySource[];
  docketLive: LiveEnvelope<DocketLiveSummary> | null;
}) {
  return (
    <div className="space-y-3">
      {docketLive && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">
                Regulations.gov Docket
              </div>
              <div className="mt-0.5 text-sm font-semibold text-zinc-100">
                {docketLive.data?.docket_id ?? "FDA-2025-N-6895"}
              </div>
            </div>
            <LiveBadge status={docketLive.status} fetchedAt={docketLive.fetched_at} />
          </div>
          <div className="mt-2 grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="text-zinc-500">Comments</div>
              <div className="text-sm font-semibold text-zinc-100">
                {docketLive.data?.comments_count ?? "—"}
              </div>
            </div>
            <div>
              <div className="text-zinc-500">Last comment</div>
              <div className="text-sm font-semibold text-zinc-100">
                {docketLive.data?.last_comment_posted_at?.slice(0, 10) ?? "—"}
              </div>
            </div>
          </div>
          {docketLive.data?.docket_url && (
            <a
              href={docketLive.data.docket_url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-[11px] text-blue-400 hover:underline"
            >
              Open docket →
            </a>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {sources.map((s) => (
          <a
            key={s.url}
            href={s.url}
            target="_blank"
            rel="noreferrer"
            className="block rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 transition-colors hover:border-blue-500/40 hover:bg-blue-500/5"
          >
            <div className="text-sm font-semibold text-zinc-100">{s.label}</div>
            <p className="mt-1 text-xs text-zinc-400">{s.description}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
