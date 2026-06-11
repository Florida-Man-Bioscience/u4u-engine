"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./auth";

/**
 * Wrap pages that require a logged-in user. While auth is still
 * resolving (hydrating from localStorage + verifying via /auth/me) we
 * render a quiet loading placeholder; once we know there's no user, we
 * push the browser to /login with a ?next= back-pointer so a successful
 * sign-in returns the user to where they started.
 *
 * Keeps the redirect concern out of every page component.
 */
// Build-time escape hatch — when NEXT_PUBLIC_AUTH_DISABLED=1 is passed to
// the build, RequireAuth passes through and we don't bounce 401s to /login.
// Useful for demos / live-deploy access while the auth surface is in flux.
const AUTH_DISABLED = process.env.NEXT_PUBLIC_AUTH_DISABLED === "1";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (AUTH_DISABLED) return;
    if (loading) return;
    if (user) return;
    const next = encodeURIComponent(pathname || "/");
    router.replace(`/login?next=${next}`);
  }, [user, loading, pathname, router]);

  if (AUTH_DISABLED) return <>{children}</>;
  if (loading || !user) {
    return (
      <div className="p-6 text-sm text-slate-500">Loading…</div>
    );
  }
  return <>{children}</>;
}
