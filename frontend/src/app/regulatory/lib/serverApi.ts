import type {
  RegulatoryEventsPayload,
  RegulatoryPeptidesPayload,
} from "../../lib/types";

/**
 * SSR-only base URL. The browser bundle uses NEXT_PUBLIC_API_BASE (often a
 * relative `/api/v1` path), which the Next server cannot fetch — server
 * fetch requires an absolute URL.
 *
 * Resolution order:
 *   1. INTERNAL_API_BASE — set this in compose to `http://api:8000`.
 *   2. NEXT_PUBLIC_API_BASE if it already looks absolute.
 *   3. Fall back to the compose service name, then localhost for `npm run dev`.
 */
function serverApiBase(): string {
  const internal = process.env.INTERNAL_API_BASE;
  if (internal) return internal.replace(/\/$/, "");
  const pub = process.env.NEXT_PUBLIC_API_BASE;
  if (pub && /^https?:\/\//i.test(pub)) return pub.replace(/\/$/, "");
  return "http://api:8000";
}

const REVALIDATE_SECONDS = 3600;

/**
 * Fetch the curated regulatory payload at SSR time. `include_live=false`
 * keeps this off the upstream API path so the request returns immediately
 * — the client component hydrates live numbers after mount.
 *
 * Returns null on any failure so the page can still render and fall back
 * to the client-side fetch path.
 */
export async function fetchRegulatoryPeptidesSSR(): Promise<RegulatoryPeptidesPayload | null> {
  try {
    const res = await fetch(
      `${serverApiBase()}/regulatory/peptides?include_live=false`,
      { next: { revalidate: REVALIDATE_SECONDS } },
    );
    if (!res.ok) return null;
    return (await res.json()) as RegulatoryPeptidesPayload;
  } catch {
    return null;
  }
}

export async function fetchRegulatoryEventsSSR(): Promise<RegulatoryEventsPayload | null> {
  try {
    const res = await fetch(
      `${serverApiBase()}/regulatory/events?include_live=false`,
      { next: { revalidate: REVALIDATE_SECONDS } },
    );
    if (!res.ok) return null;
    return (await res.json()) as RegulatoryEventsPayload;
  } catch {
    return null;
  }
}
