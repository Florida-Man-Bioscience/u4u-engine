import { NextRequest } from "next/server";

const UPSTREAM =
  process.env.OWUI_UPSTREAM ?? "http://lab-chat.theswamp.svc:8080";

function targetUrl(req: NextRequest, suffix: string) {
  const u = new URL(
    suffix.startsWith("/") ? suffix : `/${suffix}`,
    UPSTREAM.endsWith("/") ? UPSTREAM : `${UPSTREAM}/`,
  );
  u.search = req.nextUrl.search;
  return u;
}

function publicLocation(raw: string): string {
  try {
    const lu = new URL(raw, "https://flmanbiosci.net");
    let path = lu.pathname;
    if (
      path.startsWith("/static/") ||
      path.startsWith("/_app/") ||
      path.startsWith("/api/") ||
      path.startsWith("/openai/") ||
      path.startsWith("/ollama/") ||
      path.startsWith("/ws")
    ) {
      if (!path.startsWith("/owui")) path = `/owui${path}`;
    }
    if (lu.hostname.includes("lab-chat") || lu.hostname.includes("theswamp")) {
      return `${path}${lu.search}`;
    }
    if (path !== lu.pathname) return `${path}${lu.search}`;
  } catch {
    /* keep */
  }
  return raw;
}

function rewriteBody(
  text: string,
  contentType: string,
  kitBase: string,
): string {
  let t = text.replaceAll(
    'const _="Open WebUI",a=""',
    'const _="Open WebUI",a="/owui"',
  );
  if (kitBase) {
    t = t.replaceAll('base: ""', `base: "${kitBase}"`);
    t = t.replaceAll("base: ''", `base: '${kitBase}'`);
  } else {
    t = t.replaceAll('base: "/owui"', 'base: ""');
  }
  t = t.replaceAll('fetch("/api/', 'fetch("/owui/api/');
  t = t.replaceAll("fetch('/api/", "fetch('/owui/api/");
  t = t.replaceAll('"/openai/', '"/owui/openai/');
  t = t.replaceAll("'/openai/", "'/owui/openai/");
  t = t.replaceAll('"/ollama/', '"/owui/ollama/');
  t = t.replaceAll("'/ollama/", "'/owui/ollama/");
  t = t.replaceAll('"/static/splash', '"/owui/static/splash');
  t = t.replaceAll("'/static/splash", "'/owui/static/splash");
  t = t.replaceAll("/owui/owui/", "/owui/");
  if (contentType.includes("html") || contentType.includes("javascript")) {
    t = t.replace(/\.js\?v=owui2/g, ".js");
    t = t.replace(/\.js(["'])/g, ".js?v=owui2$1");
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

export async function proxyOwui(
  req: NextRequest,
  suffix: string,
  kitBase = "/owui",
) {
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
    r = await fetch(targetUrl(req, suffix), init);
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
    const text = rewriteBody(await r.text(), ct, kitBase);
    return new Response(text, { status: r.status, headers: out });
  }
  return new Response(r.body, { status: r.status, headers: out });
}

export function owuiSuffix(path?: string[]) {
  return path?.length ? `/owui/${path.join("/")}` : "/owui/";
}

export function authSuffix(path?: string[]) {
  return path?.length ? `/owui/auth/${path.join("/")}` : "/owui/auth";
}
