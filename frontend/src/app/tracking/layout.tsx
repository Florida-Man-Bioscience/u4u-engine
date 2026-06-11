import { RequireAuth } from "../lib/RequireAuth";

export default function TrackingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
