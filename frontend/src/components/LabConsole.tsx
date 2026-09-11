"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Provider = {
  id: string;
  label: string;
  models: string[];
  default_model: string;
  key_configured: boolean;
};

type Health = {
  ok?: boolean;
  error?: string;
  profile?: string;
  providers?: Provider[];
  default_provider?: string;
};

export function LabConsole() {
  const [health, setHealth] = useState<Health | null>(null);
  const [token, setToken] = useState("");
  const [provider, setProvider] = useState("neuralwatt");
  const [model, setModel] = useState("");
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/lab/health", { cache: "no-store" })
      .then(async (r) => {
        const raw = await r.text();
        try {
          return JSON.parse(raw) as Health;
        } catch {
          throw new Error(raw.slice(0, 180) || `HTTP ${r.status}`);
        }
      })
      .then((j) => {
        if (cancelled) return;
        setHealth(j);
        const pid = j.default_provider || j.providers?.[0]?.id || "neuralwatt";
        setProvider(pid);
        const spec = (j.providers || []).find((p) => p.id === pid);
        setModel(spec?.default_model || spec?.models[0] || "");
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

  const providers = health?.providers || [];
  const current = useMemo(
    () => providers.find((p) => p.id === provider),
    [providers, provider],
  );

  function onProviderChange(id: string) {
    setProvider(id);
    const spec = providers.find((p) => p.id === id);
    setModel(spec?.default_model || spec?.models[0] || "");
  }

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
        body: JSON.stringify({ message, provider, model }),
      });
      const raw = await r.text();
      let j: {
        text?: string;
        reply?: string;
        error?: string;
        stderr_tail?: string;
        ok?: boolean;
      };
      try {
        j = JSON.parse(raw) as typeof j;
      } catch {
        setReply(raw.slice(0, 2000) || `HTTP ${r.status}`);
        return;
      }
      const main = j.text || j.reply || j.error || JSON.stringify(j);
      setReply(
        j.ok === false && j.stderr_tail
          ? `${main}\n\n${j.stderr_tail}`
          : main,
      );
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
        <div className="grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm">
            Provider
            <select
              value={provider}
              onChange={(e) => onProviderChange(e.target.value)}
              className="min-h-11 rounded-lg border border-[#d4c4a8] px-3"
            >
              {providers.length === 0 ? (
                <option value={provider}>{provider}</option>
              ) : (
                providers.map((p) => (
                  <option key={p.id} value={p.id} disabled={!p.key_configured}>
                    {p.label}
                    {p.key_configured ? "" : " (no key)"}
                  </option>
                ))
              )}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            Model
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="min-h-11 rounded-lg border border-[#d4c4a8] px-3"
            >
              {(current?.models || (model ? [model] : [])).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
        </div>
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
          disabled={busy || !live || (current ? !current.key_configured : false)}
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
