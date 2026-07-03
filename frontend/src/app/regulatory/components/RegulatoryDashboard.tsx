"use client";

import { useEffect, useState } from "react";
import {
  getRegulatoryEvents,
  getRegulatoryPeptides,
} from "../../lib/api";
import type {
  RegulatoryEventsPayload,
  RegulatoryPeptidesPayload,
} from "../../lib/types";
import { CriticalDatesTable } from "./CriticalDatesTable";
import { EventTimeline } from "./EventTimeline";
import { PeptideGrid } from "./PeptideGrid";
import { SourcesGrid } from "./SourcesGrid";
import { StatsRow } from "./StatsRow";

interface Props {
  initialPeptides: RegulatoryPeptidesPayload | null;
  initialEvents: RegulatoryEventsPayload | null;
}

/**
 * Renders the dashboard, hydrating live source data after mount.
 *
 * When the server prefetched the curated baseline (the common case), the
 * page paints from `initial*` on the first frame and the post-mount fetch
 * just swaps in live envelopes (active trial counts, recall totals,
 * docket comment counts). When the SSR fetch failed (backend down at
 * build/request time), we fall back to a client-side fetch with the same
 * loading state the page used to have.
 */
export function RegulatoryDashboard({ initialPeptides, initialEvents }: Props) {
  const [peptides, setPeptides] = useState<RegulatoryPeptidesPayload | null>(
    initialPeptides,
  );
  const [events, setEvents] = useState<RegulatoryEventsPayload | null>(
    initialEvents,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getRegulatoryPeptides(), getRegulatoryEvents()])
      .then(([p, e]) => {
        if (cancelled) return;
        setPeptides(p);
        setEvents(e);
      })
      .catch((err) => {
        if (cancelled) return;
        // Don't blow away an already-rendered SSR baseline just because
        // the live augment fetch failed — log it via the error banner
        // but keep showing curated data.
        setError(err.message ?? "Failed to load regulatory data");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="relative left-1/2 right-1/2 -mx-[50vw] -my-8 w-screen bg-[#0d0f14] text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <header className="mb-8 border-b border-zinc-800 pb-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                FDA Peptide Regulatory Dashboard
              </h1>
              <p className="mt-1 text-sm text-zinc-400">
                503A Bulks List status, PCAC review schedule, and live regulatory
                signals — curated baseline augmented with ClinicalTrials.gov,
                openFDA, and Federal Register data.
              </p>
            </div>
            {peptides?.last_curated && (
              <span className="rounded-full border border-zinc-700 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-400">
                Curated {peptides.last_curated}
              </span>
            )}
          </div>
        </header>

        {error && !peptides && (
          <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            <p className="font-semibold">Could not reach the regulatory API.</p>
            <p className="mt-1 text-xs opacity-80">{error}</p>
            <p className="mt-2 text-xs opacity-80">
              The backend serves the curated baseline at{" "}
              <code className="rounded bg-black/30 px-1">/regulatory/peptides</code>{" "}
              and{" "}
              <code className="rounded bg-black/30 px-1">/regulatory/events</code>.
            </p>
          </div>
        )}

        {!peptides || !events ? (
          <div className="rounded-lg border border-zinc-800 p-8 text-center text-sm text-zinc-500">
            Loading regulatory data…
          </div>
        ) : (
          <div className="space-y-10">
            <section>
              <StatsRow payload={peptides} />
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold">Peptide Status</h2>
              <PeptideGrid payload={peptides} />
            </section>

            <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div>
                <h2 className="mb-3 text-lg font-semibold">Critical Dates</h2>
                <CriticalDatesTable events={events.events} />
              </div>
              <div>
                <h2 className="mb-3 text-lg font-semibold">Timeline</h2>
                <EventTimeline events={events.events} />
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold">Official Sources</h2>
              <SourcesGrid
                sources={events.official_sources}
                docketLive={events.docket_live}
              />
              {events.pcac_contact && (
                <p className="mt-3 text-xs text-zinc-500">
                  PCAC contact: {events.pcac_contact.name} (
                  <a
                    href={`mailto:${events.pcac_contact.email}`}
                    className="text-blue-400 hover:underline"
                  >
                    {events.pcac_contact.email}
                  </a>
                  ) — {events.pcac_contact.role}
                </p>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
