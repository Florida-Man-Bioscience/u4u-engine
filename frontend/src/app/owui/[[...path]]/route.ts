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

function rewriteBody(text: string, contentType: string): string {
  let t = text.replaceAll(
    'const _="Open WebUI",a=""',
    'const _="Open WebUI",a="/owui"',
  );
  t = t.replaceAll("fetch(\"/api/", "fetch(\"/owui/api/");
  t = t.replaceAll("fetch('/api/", "fetch('/owui/api/");
  t = t.replaceAll('`${A}/api/', '`${A}/api/');
  t = t.replaceAll('"/openai/', '"/owui/openai/');
  t = t.replaceAll("'/openai/", "'/owui/openai/");
  t = t.replaceAll('"/ollama/', '"/owui/ollama/');
  t = t.replaceAll("'/ollama/", "'/owui/ollama/");
  t = t.replaceAll("/owui/owui/", "/owui/");
  if (contentType.includes("html")) {
    t = t.replace(
      /(\/owui\/_app\/immutable\/[^"' ]+\.js)/g,
      "$1?v=owui2",
    );
  }
  return t;
}

function isText(ct: string): boolean {
  return (
    ct.includes("text/") ||
    ct.includes("javascript") ||
    ct.includes("json") ||
    ct.includes("xml")
  );
}

async function proxy(req: NextRequest, path?: string[]) {
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.set("accept-encoding", "identity");
  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
    cache: "no-store",
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
  const ct = r.headers.get("content-type") || "";
  const out = new Headers(r.headers);
  const loc = out.get("location");
  if (loc) out.set("location", publicLocation(loc));
  out.delete("content-encoding");
  out.delete("transfer-encoding");
  out.delete("content-length");
  out.set("cache-control", "no-store, no-cache, must-revalidate");
  out.set("cdn-cache-control", "no-store");

  if (req.method !== "HEAD" && isText(ct)) {
    const text = rewriteBody(await r.text(), ct);
    return new Response(text, { status: r.status, headers: out });
  }
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
