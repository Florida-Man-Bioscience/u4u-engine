"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";

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

type Attachment = {
  name: string;
  path: string;
  size: number;
  content_type: string;
  download_url?: string;
};

type Turn = {
  role: "user" | "assistant";
  content: string;
  attachments?: Attachment[];
};

const MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024;

const humanBytes = (size: number) => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

export function LabConsole() {
  const [health, setHealth] = useState<Health | null>(null);
  const [token, setToken] = useState("");
  const [provider, setProvider] = useState("neuralwatt");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState("");
  const [thread, setThread] = useState<Turn[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [files, setFiles] = useState<Attachment[]>([]);
  const [busy, setBusy] = useState(false);
  const [fileBusy, setFileBusy] = useState(false);
  const [fileError, setFileError] = useState("");
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
    .map((t) => (t.engine_version ? `${t.id} v${t.engine_version}` : t.id))
    .join(" · ");
  const authorization = token.trim() ? `Bearer ${token.trim()}` : "";

  function onProviderChange(id: string) {
    setProvider(id);
    const spec = providers.find((p) => p.id === id);
    setModel(spec?.default_model || spec?.models[0] || "");
  }

  async function refreshFiles() {
    if (!authorization) {
      setFileError("Enter the shared token before listing files.");
      return;
    }
    setFileError("");
    try {
      const response = await fetch("/api/lab/files", {
        headers: { authorization },
        cache: "no-store",
      });
      const body = (await response.json()) as { files?: Attachment[]; error?: string };
      if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
      setFiles(body.files || []);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "file_list_failed");
    }
  }

  async function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files || []);
    event.currentTarget.value = "";
    if (selected.length === 0) return;
    if (!authorization) {
      setFileError("Enter the shared token before uploading files.");
      return;
    }
    setFileBusy(true);
    setFileError("");
    try {
      const form = new FormData();
      selected.forEach((file) => form.append("files", file, file.name));
      const response = await fetch("/api/lab/files", {
        method: "POST",
        headers: { authorization },
        body: form,
      });
      const body = (await response.json()) as {
        files?: Attachment[];
        error?: string;
      };
      if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
      setAttachments((currentAttachments) => [
        ...currentAttachments,
        ...(body.files || []),
      ]);
      await refreshFiles();
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "file_upload_failed");
    } finally {
      setFileBusy(false);
    }
  }

  async function downloadFile(file: Attachment) {
    if (!authorization) {
      setFileError("Enter the shared token before downloading files.");
      return;
    }
    setFileError("");
    try {
      const response = await fetch(
        `/api/lab/files?path=${encodeURIComponent(file.path)}`,
        { headers: { authorization }, cache: "no-store" },
      );
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { error?: string };
        throw new Error(body.error || `HTTP ${response.status}`);
      }
      const rawSize = response.headers.get("content-length");
      const declaredSize = rawSize === null ? 0 : Number(rawSize);
      if (rawSize !== null && (!Number.isSafeInteger(declaredSize) || declaredSize > MAX_DOWNLOAD_BYTES)) {
        throw new Error("file_too_large");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "file_download_failed");
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = message.trim();
    if (!text || busy || fileBusy) return;
    const userTurn: Turn = {
      role: "user",
      content: text,
      ...(attachments.length ? { attachments } : {}),
    };
    const nextThread: Turn[] = [...thread, userTurn];
    setThread(nextThread);
    setMessage("");
    setAttachments([]);
    setBusy(true);
    try {
      const r = await fetch("/api/lab/turn", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization,
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
            {" "}· <span className="font-mono text-xs">{toolsLine}</span>
          </>
        ) : null}
      </p>
      <p className="mt-1 text-xs text-[#6b5d4d]">
        Follow-ups stay in this thread. Uploads are available to the lab in
        <code className="mx-1 font-mono">uploads/</code>; ask it to save downloadable
        artifacts in <code className="mx-1 font-mono">outputs/</code>.
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
              {t.attachments?.length ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {t.attachments.map((file) => (
                    <span
                      key={file.path}
                      className="rounded-full border border-[#d4c4a8] bg-white px-3 py-1 text-xs"
                    >
                      {file.name}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          {busy ? <p className="font-mono text-[11px] text-[#6b5d4d]">Running…</p> : null}
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
                    {p.label}{p.key_configured ? "" : " (bring your key)"}
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
                <option key={m} value={m}>{m}</option>
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
          Attach files
          <input
            type="file"
            multiple
            onChange={onFileChange}
            disabled={fileBusy || !authorization}
            className="min-h-11 rounded-lg border border-[#d4c4a8] px-3 py-2 text-sm"
          />
        </label>
        {attachments.length ? (
          <div className="flex flex-wrap gap-2">
            {attachments.map((file) => (
              <button
                key={file.path}
                type="button"
                onClick={() => setAttachments((currentFiles) => currentFiles.filter((f) => f.path !== file.path))}
                className="rounded-full border border-[#d4c4a8] px-3 py-1 text-xs"
                title="Remove from next turn"
              >
                {file.name} ×
              </button>
            ))}
          </div>
        ) : null}
        <label className="grid gap-1 text-sm">
          Message
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            className="rounded-lg border border-[#d4c4a8] px-3 py-2"
            placeholder="Ask the lab to read an attachment or save a result under outputs/."
            required
          />
        </label>
        {fileError ? <p className="text-sm text-[#8a3b2a]">{fileError}</p> : null}
        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={busy || fileBusy || !live || !authorization || (current ? !current.key_configured && !apiKey.trim() : false)}
            className="min-h-11 rounded-full bg-[#1a6b4a] px-6 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Running…" : thread.length ? "Send follow-up" : "Send"}
          </button>
          <button
            type="button"
            onClick={() => { setThread([]); setAttachments([]); }}
            disabled={busy || fileBusy || thread.length === 0}
            className="min-h-11 rounded-full border border-[#d4c4a8] px-6 text-sm font-semibold text-[#1a1612] disabled:opacity-50"
          >
            New thread
          </button>
          <button
            type="button"
            onClick={refreshFiles}
            disabled={fileBusy || !authorization}
            className="min-h-11 rounded-full border border-[#d4c4a8] px-6 text-sm font-semibold text-[#1a1612] disabled:opacity-50"
          >
            Refresh files
          </button>
        </div>
      </form>
      {files.length ? (
        <div className="mt-6 rounded-lg border border-[#edecea] bg-[#f4efe6] p-3">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#1a6b4a]">
            Workspace files
          </p>
          <div className="mt-2 grid gap-2">
            {files.map((file) => (
              <div key={file.path} className="flex items-center justify-between gap-3 rounded bg-white px-3 py-2 text-sm">
                <span className="min-w-0 truncate" title={file.path}>
                  {file.path} <span className="text-xs text-[#6b5d4d]">({humanBytes(file.size)})</span>
                </span>
                <button
                  type="button"
                  onClick={() => downloadFile(file)}
                  className="shrink-0 rounded-full border border-[#d4c4a8] px-3 py-1 text-xs font-semibold"
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
