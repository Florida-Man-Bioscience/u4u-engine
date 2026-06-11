import { RequireAuth } from "../lib/RequireAuth";

export default function JobsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
