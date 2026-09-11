import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const UPSTREAM =
  process.env.LAB_UPSTREAM ?? "http://di-lab.theswamp.svc:8080";

export async function GET() {
  try {
    const r = await fetch(`${UPSTREAM}/health`, { cache: "no-store" });
    const body = await r.json().catch(() => ({}));
    return NextResponse.json(body, { status: r.status });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      { ok: false, error: "lab_unreachable", detail: msg },
      { status: 503 },
    );
  }
}
