"use client";

import { FormEvent, useEffect, useState } from "react";

type Health = { ok?: boolean; error?: string; profile?: string };

export function LabConsole() {
  const [health, setHealth] = useState<Health | null>(null);
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/lab/health", { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => {
        if (!cancelled) setHealth(j);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setHealth({
            ok: false,
            error: e instanceof Error ? e.message : "unreachable",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setReply("");
    try {
      const r = await fetch("/api/lab/turn", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
      });
      const j = (await r.json()) as { reply?: string; error?: string };
      setReply(j.reply || j.error || JSON.stringify(j));
    } catch (err) {
      setReply(err instanceof Error ? err.message : "request_failed");
    } finally {
      setBusy(false);
    }
  }

  const live = health?.ok === true;

  return (
    <div
      id="lab-console"
      className="mt-10 rounded-2xl border border-[#d4c4a8] bg-white p-6 text-[#1a1612]"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#6b5d4d]">
        Lab console · same origin
      </p>
      <p className="mt-2 text-sm text-[#4a4036]">
        Status:{" "}
        <span className={live ? "text-[#1a6b4a]" : "text-[#8a3b2a]"}>
          {live ? "reachable" : health?.error || "checking…"}
        </span>
      </p>
      <form onSubmit={onSubmit} className="mt-4 grid gap-3">
        <label className="grid gap-1 text-sm">
          Shared token
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="min-h-11 rounded-lg border border-[#d4c4a8] px-3"
            required
          />
        </label>
        <label className="grid gap-1 text-sm">
          Message
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            className="rounded-lg border border-[#d4c4a8] px-3 py-2"
            required
          />
        </label>
        <button
          type="submit"
          disabled={busy || !live}
          className="min-h-11 rounded-full bg-[#1a6b4a] px-6 text-sm font-semibold text-white disabled:opacity-50"
        >
          {busy ? "Running…" : "Send turn"}
        </button>
      </form>
      {reply ? (
        <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-lg bg-[#f4efe6] p-4 text-sm">
          {reply}
        </pre>
      ) : null}
    </div>
  );
}
