import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const UPSTREAM =
  process.env.LAB_UPSTREAM ?? "http://di-lab.theswamp.svc:8080";
const MAX_REQUEST_BYTES = 25 * 1024 * 1024;
const MAX_RESPONSE_BYTES = 1024 * 1024;

function authHeaders(req: Request): HeadersInit {
  const auth = req.headers.get("authorization") || "";
  return auth ? { authorization: auth } : {};
}

async function boundedText(response: Response): Promise<string> {
  const declared = response.headers.get("content-length");
  if (declared) {
    const size = Number(declared);
    if (!Number.isSafeInteger(size) || size > MAX_RESPONSE_BYTES) {
      throw new Error("upstream_response_too_large");
    }
  }
  if (!response.body) return "";
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const next = await reader.read();
    if (next.done) break;
    total += next.value.byteLength;
    if (total > MAX_RESPONSE_BYTES) {
      await reader.cancel();
      throw new Error("upstream_response_too_large");
    }
    chunks.push(next.value);
  }
  const merged = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(merged);
}

function errorResponse(error: unknown) {
  if (error instanceof Error && error.message === "upstream_response_too_large") {
    return NextResponse.json(
      { ok: false, error: "upstream_response_too_large" },
      { status: 502 },
    );
  }
  return NextResponse.json(
    {
      ok: false,
      error: "lab_unreachable",
      detail: error instanceof Error ? error.message : String(error),
    },
    { status: 503 },
  );
}

function forwardedHeaders(upstream: Response) {
  const headers = new Headers();
  for (const name of [
    "content-type",
    "content-disposition",
    "content-length",
    "cache-control",
    "x-content-type-options",
  ]) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  return headers;
}

export async function GET(req: Request) {
  const url = new URL(`${UPSTREAM}/api/v1/files`);
  url.search = new URL(req.url).search;
  try {
    const upstream = await fetch(url, {
      headers: authHeaders(req),
      cache: "no-store",
    });
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: forwardedHeaders(upstream),
    });
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(req: Request) {
  const rawLength = req.headers.get("content-length");
  if (!rawLength) {
    return NextResponse.json(
      { ok: false, error: "content_length_required" },
      { status: 411 },
    );
  }
  const contentLength = Number(rawLength);
  if (!Number.isSafeInteger(contentLength) || contentLength < 0) {
    return NextResponse.json(
      { ok: false, error: "bad_content_length" },
      { status: 400 },
    );
  }
  if (contentLength > MAX_REQUEST_BYTES) {
    return NextResponse.json({ ok: false, error: "request_too_large" }, { status: 413 });
  }
  if (!req.body) {
    return NextResponse.json({ ok: false, error: "body_required" }, { status: 400 });
  }
  try {
    const upstream = await fetch(`${UPSTREAM}/api/v1/files`, {
      method: "POST",
      headers: {
        ...authHeaders(req),
        "content-type": req.headers.get("content-type") || "",
        "content-length": String(contentLength),
      },
      body: req.body,
      duplex: "half",
    } as RequestInit & { duplex: "half" });
    const raw = await boundedText(upstream);
    let payload: unknown;
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = { ok: false, error: "upstream_not_json", detail: raw.slice(0, 240) };
    }
    return NextResponse.json(payload, { status: upstream.status });
  } catch (error) {
    return errorResponse(error);
  }
}
