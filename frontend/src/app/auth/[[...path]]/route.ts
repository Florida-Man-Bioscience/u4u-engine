import { NextRequest, NextResponse } from "next/server";
import { authSuffix, proxyOwui } from "@/lib/owui-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const rest = path?.length ? `/${path.join("/")}` : "";
  const host =
    req.headers.get("x-forwarded-host") ||
    req.headers.get("host") ||
    "flmanbiosci.net";
  const proto = req.headers.get("x-forwarded-proto") || "https";
  return NextResponse.redirect(
    `${proto}://${host}/owui/auth${rest}${req.nextUrl.search}`,
    302,
  );
}

async function handle(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxyOwui(req, authSuffix(path));
}

export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
