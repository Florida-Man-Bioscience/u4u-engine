import { RegulatoryDashboard } from "./components/RegulatoryDashboard";
import {
  fetchRegulatoryEventsSSR,
  fetchRegulatoryPeptidesSSR,
} from "./lib/serverApi";

// Re-render the SSR shell at most once an hour. The curated JSON only
// changes when someone edits data/regulatory/*.json; live augments
// hydrate client-side regardless.
export const revalidate = 3600;

export default async function RegulatoryDashboardPage() {
  const [initialPeptides, initialEvents] = await Promise.all([
    fetchRegulatoryPeptidesSSR(),
    fetchRegulatoryEventsSSR(),
  ]);

  return (
    <RegulatoryDashboard
      initialPeptides={initialPeptides}
      initialEvents={initialEvents}
    />
  );
}
