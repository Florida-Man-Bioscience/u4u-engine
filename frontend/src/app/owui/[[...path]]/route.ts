import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const CONSOLE =
  "https://flmanbiosci.net/products/discovery-informatics#lab-console";

/** /owui is retired. Dedicated host is IAC. Public UI is the one-shot console. */
function redirect(_req: NextRequest) {
  return NextResponse.redirect(CONSOLE, 302);
}

export const GET = redirect;
export const POST = redirect;
export const PUT = redirect;
export const PATCH = redirect;
export const DELETE = redirect;
export const HEAD = redirect;
export const OPTIONS = redirect;
