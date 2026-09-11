import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const UPSTREAM =
  process.env.LAB_UPSTREAM ?? "http://di-lab.theswamp.svc:8080";

export async function POST(req: Request) {
  const auth = req.headers.get("authorization") || "";
  let payload: unknown;
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "bad_json" }, { status: 400 });
  }
  try {
    const r = await fetch(`${UPSTREAM}/api/v1/turn`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: auth,
      },
      body: JSON.stringify(payload),
    });
    const raw = await r.text();
    let body: unknown;
    try {
      body = JSON.parse(raw);
    } catch {
      body = {
        ok: false,
        error: "upstream_not_json",
        detail: raw.slice(0, 240),
      };
    }
    const status =
      typeof body === "object" &&
      body !== null &&
      "ok" in body &&
      (body as { ok?: boolean }).ok === false &&
      r.status >= 500
        ? 200
        : r.status;
    return NextResponse.json(body, { status });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      { ok: false, error: "lab_unreachable", detail: msg },
      { status: 503 },
    );
  }
}
