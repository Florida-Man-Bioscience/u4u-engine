import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const UPSTREAM =
  process.env.OWUI_UPSTREAM ?? "http://lab-chat.theswamp.svc:8080";

function target(req: NextRequest, path?: string[]) {
  const suffix = path?.length ? `/owui/${path.join("/")}` : "/owui/";
  const u = new URL(suffix, UPSTREAM.endsWith("/") ? UPSTREAM : `${UPSTREAM}/`);
  u.search = req.nextUrl.search;
  return u;
}

function publicLocation(raw: string): string {
  try {
    const lu = new URL(raw, UPSTREAM);
    if (
      lu.hostname.includes("lab-chat") ||
      lu.hostname.includes("theswamp") ||
      lu.hostname === "localhost"
    ) {
      return `${lu.pathname}${lu.search}`;
    }
  } catch {
    /* keep */
  }
  return raw;
}

async function proxy(req: NextRequest, path?: string[]) {
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");
  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
    init.body = req.body;
    Object.assign(init, { duplex: "half" });
  }
  let r: Response;
  try {
    r = await fetch(target(req, path), init);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(`owui_unreachable: ${msg}`, { status: 503 });
  }
  const out = new Headers(r.headers);
  const loc = out.get("location");
  if (loc) out.set("location", publicLocation(loc));
  out.delete("content-encoding");
  out.delete("transfer-encoding");
  return new Response(r.body, { status: r.status, headers: out });
}

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function HEAD(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function OPTIONS(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
