import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { PRODUCT_HOST } from "@/lib/site";

function hostOnly(host: string | null): string {
  if (!host) return "";
  return host.split(":")[0].toLowerCase();
}

/**
 * Host-aware routing helpers.
 *
 * Cross-host apex → product redirects belong in the Cilium HTTPRoute
 * (iac theswamp/httproute.yaml) and must ship **with** DNS for
 * peptodyssey.flmanbiosci.net. Doing them in Next alone ships a 301 to a
 * host that does not resolve yet and breaks the frozen TestFlight URL
 * https://flmanbiosci.net/peptodyssey/privacy (must end 200).
 *
 * Until gateway+DNS cutover, company apex and app.* continue to serve the
 * product tree in-process (same Next deployment).
 */
export function middleware(request: NextRequest) {
  const host = hostOnly(request.headers.get("host"));
  const { pathname } = request.nextUrl;

  // Product host: keep /peptodyssey/privacy as alias → /privacy (canonical).
  if (host === PRODUCT_HOST) {
    if (
      pathname === "/peptodyssey/privacy" ||
      pathname.startsWith("/peptodyssey/privacy/")
    ) {
      const url = request.nextUrl.clone();
      url.pathname = "/privacy";
      return NextResponse.redirect(url, 301);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Skip Next internals and static files.
     */
    "/((?!_next/static|_next/image|favicon.ico|assets/).*)",
  ],
};
