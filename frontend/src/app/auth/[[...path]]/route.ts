import { NextRequest, NextResponse } from "next/server";
import { authSuffix, proxyOwui } from "@/lib/owui-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const url = req.nextUrl.clone();
  const rest = path?.length ? `/${path.join("/")}` : "";
  url.pathname = `/owui/auth${rest}`;
  return NextResponse.redirect(url, 302);
}

async function handle(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxyOwui(req, authSuffix(path));
}

export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const HEAD = GET;
export const OPTIONS = handle;
