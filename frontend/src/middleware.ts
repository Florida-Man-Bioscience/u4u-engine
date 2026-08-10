import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { COMPANY_HOST, PRODUCT_HOST, PRODUCT_ORIGIN } from "@/lib/site";

/** Paths that belong on the PeptOdyssey product host. */
const PRODUCT_PREFIXES = [
  "/jobs",
  "/tracking",
  "/regulatory",
  "/study",
  "/faq",
  "/peptodyssey",
  "/privacy",
  "/api/v1",
];

function hostOnly(host: string | null): string {
  if (!host) return "";
  return host.split(":")[0].toLowerCase();
}

export function middleware(request: NextRequest) {
  const host = hostOnly(request.headers.get("host"));
  const { pathname, search } = request.nextUrl;

  // Apex / www: send product traffic to the product subdomain.
  if (host === COMPANY_HOST || host === `www.${COMPANY_HOST}`) {
    if (pathname === "/peptodyssey/privacy" || pathname.startsWith("/peptodyssey/privacy/")) {
      const url = new URL(`${PRODUCT_ORIGIN}/privacy`);
      url.search = search;
      return NextResponse.redirect(url, 301);
    }
    if (PRODUCT_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
      const url = new URL(`${PRODUCT_ORIGIN}${pathname}${search}`);
      return NextResponse.redirect(url, 301);
    }
  }

  // Product host: keep /peptodyssey/privacy as alias → /privacy
  if (host === PRODUCT_HOST) {
    if (pathname === "/peptodyssey/privacy" || pathname.startsWith("/peptodyssey/privacy/")) {
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
