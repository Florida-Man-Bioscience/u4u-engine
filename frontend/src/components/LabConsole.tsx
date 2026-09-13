"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type Provider = {
  id: string;
  label: string;
  models: string[];
  default_model: string;
  key_configured: boolean;
};

type LabTool = {
  id: string;
  engine_version?: string;
  cli?: string;
};

type Health = {
  ok?: boolean;
  error?: string;
  profile?: string;
  providers?: Provider[];
  default_provider?: string;
  tools?: LabTool[];
};

type Turn = { role: "user" | "assistant"; content: string };

export function LabConsole() {
  const [health, setHealth] = useState<Health | null>(null);
  const [token, setToken] = useState("");
  const [provider, setProvider] = useState("neuralwatt");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState("");
  const [thread, setThread] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [thread, busy]);

  const providers = health?.providers || [];
  const current = useMemo(
    () => providers.find((p) => p.id === provider),
    [providers, provider],
  );
  const toolsLine = (health?.tools || [])
    .map((t) =>
      t.engine_version ? `${t.id} v${t.engine_version}` : t.id,
    )
    .join(" · ");

  function onProviderChange(id: string) {
    setProvider(id);
    const spec = providers.find((p) => p.id === id);
    setModel(spec?.default_model || spec?.models[0] || "");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = message.trim();
    if (!text || busy) return;
    const nextThread: Turn[] = [...thread, { role: "user", content: text }];
    setThread(nextThread);
    setMessage("");
    setBusy(true);
    try {
      const r = await fetch("/api/lab/turn", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          messages: nextThread,
          provider,
          model,
          ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
        }),
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
        setThread([
          ...nextThread,
          { role: "assistant", content: raw.slice(0, 2000) || `HTTP ${r.status}` },
        ]);
        return;
      }
      const main = j.text || j.reply || j.error || JSON.stringify(j);
      const content =
        j.ok === false && j.stderr_tail ? `${main}\n\n${j.stderr_tail}` : main;
      setThread([...nextThread, { role: "assistant", content }]);
    } catch (err) {
      setThread([
        ...nextThread,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "request_failed",
        },
      ]);
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
        Lab console · multi-shot
      </p>
      <p className="mt-2 text-sm text-[#4a4036]">
        Status:{" "}
        <span className={live ? "text-[#1a6b4a]" : "text-[#8a3b2a]"}>
          {live ? "reachable" : health?.error || "checking…"}
        </span>
        {toolsLine ? (
          <>
            {" "}
            · <span className="font-mono text-xs">{toolsLine}</span>
          </>
        ) : null}
      </p>
      <p className="mt-1 text-xs text-[#6b5d4d]">
        Follow-ups stay in this thread. Each turn preloads{" "}
        <code className="font-mono">lit-review</code> against{" "}
        <code className="font-mono">/opt/litreview</code>.
      </p>
      {thread.length > 0 ? (
        <div className="mt-4 max-h-[28rem] space-y-3 overflow-y-auto rounded-lg border border-[#edecea] bg-[#f4efe6] p-3">
          {thread.map((t, i) => (
            <div key={`${t.role}-${i}`}>
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#1a6b4a]">
                {t.role}
              </p>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-sm">
                {t.content}
              </pre>
            </div>
          ))}
          {busy ? (
            <p className="font-mono text-[11px] text-[#6b5d4d]">Running…</p>
          ) : null}
          <div ref={bottomRef} />
        </div>
      ) : null}
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
                  <option key={p.id} value={p.id}>
                    {p.label}
                    {p.key_configured ? "" : " (bring your key)"}
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
          Provider API key (optional)
          <input
            type="password"
            autoComplete="off"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Uses yours for this turn only. Leave blank to use the jail key."
            className="min-h-11 rounded-lg border border-[#d4c4a8] px-3"
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
        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={
              busy ||
              !live ||
              (current ? !current.key_configured && !apiKey.trim() : false)
            }
            className="min-h-11 rounded-full bg-[#1a6b4a] px-6 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Running…" : thread.length ? "Send follow-up" : "Send"}
          </button>
          <button
            type="button"
            onClick={() => setThread([])}
            disabled={busy || thread.length === 0}
            className="min-h-11 rounded-full border border-[#d4c4a8] px-6 text-sm font-semibold text-[#1a1612] disabled:opacity-50"
          >
            New thread
          </button>
        </div>
      </form>
    </div>
  );
}
