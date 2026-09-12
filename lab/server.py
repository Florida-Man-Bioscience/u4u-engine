"""Thin HTTP front for the generic Hermes lab profile.

GET  /health                 — probes (no secrets)
GET  /                       — gated chat HTML
POST /api/v1/turn            — Bearer LAB_SHARED_TOKEN required
GET  /v1/models              — OpenAI list (same Bearer)
POST /v1/chat/completions    — OpenAI chat (same Bearer); used by Open WebUI
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from providers import (
    messages_to_prompt,
    openai_models,
    parse_openai_model,
    public_catalog,
    resolve_turn,
)

PORT = int(os.environ.get("PORT", "8080"))
PROFILE = os.environ.get("HERMES_PROFILE", "lab")
TOKEN = os.environ.get("LAB_SHARED_TOKEN", "")
TURN_TIMEOUT = int(os.environ.get("LAB_TURN_TIMEOUT", "120"))


def _skill_count(root: str) -> int:
    p = Path(root)
    if not p.is_dir():
        return 0
    return sum(1 for _ in p.rglob("SKILL.md"))


def health() -> dict:
    body = {
        "ok": True,
        "profile": PROFILE,
        "product": "discovery-informatics",
        "class": "lab-jail",
        "token_configured": bool(TOKEN),
        "workspace": os.environ.get("HERMES_WORKSPACE", "/data/workspace"),
        "bioskills_count": _skill_count("/opt/bioskills"),
        "science_skills_count": _skill_count("/opt/lab-science-skills"),
    }
    body.update(public_catalog())
    return body


def run_hermes(message: str, resolved: dict[str, str]) -> dict[str, object]:
    hermes = os.environ.get("HERMES_BIN", "hermes")
    cmd = [hermes]
    if PROFILE and PROFILE not in ("default", "-"):
        cmd += ["-p", PROFILE]
    cmd += [
        "chat",
        "-q",
        message,
        "-Q",
        "--provider",
        resolved["hermes_provider"],
        "-m",
        resolved["model"],
    ]
    env = {
        **os.environ,
        "HERMES_HOME": os.environ.get("HERMES_HOME", "/data/profile"),
        "HERMES_YOLO_MODE": "1",
    }
    guest = resolved.get("guest_key") or ""
    if guest:
        env[resolved["key_env"]] = guest
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TURN_TIMEOUT,
            cwd=os.environ.get("HERMES_WORKSPACE", "/data/workspace"),
            env=env,
        )
    except FileNotFoundError:
        return {"error": "hermes_missing"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}

    def _redact(s: str) -> str:
        if guest and s:
            return s.replace(guest, "***")
        return s

    return {
        "returncode": proc.returncode,
        "text": _redact(proc.stdout or "")[-12000:],
        "stderr_tail": _redact(proc.stderr or "")[-2000:],
        "byok": bool(guest),
        "provider": resolved["provider_id"],
        "model": resolved["model"],
    }


def openai_completion(model_id: str, text: str, stream: bool) -> tuple[str, str]:
    """Return (content_type, body)."""
    cid = f"chatcmpl-lab-{int(time.time())}"
    if stream:
        chunk = {
            "id": cid,
            "object": "chat.completion.chunk",
            "choices": [
                {"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}
            ],
        }
        done = {
            "id": cid,
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        body = (
            f"data: {json.dumps(chunk)}\n\n"
            f"data: {json.dumps(done)}\n\n"
            "data: [DONE]\n\n"
        )
        return "text/event-stream", body
    payload = {
        "id": cid,
        "object": "chat.completion",
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }
    return "application/json", json.dumps(payload)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _json(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, code: int, html: str) -> None:
        raw = html.encode()
        self.send_response(code)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _bytes(self, code: int, content_type: str, body: str) -> None:
        raw = body.encode()
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _route(self) -> str:
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _auth_ok(self) -> bool:
        if not TOKEN:
            self._json(503, {"ok": False, "error": "token_not_configured"})
            return False
        auth = self.headers.get("Authorization", "")
        got = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if got != TOKEN:
            self._json(401, {"ok": False, "error": "unauthorized"})
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        path = self._route()
        if path == "/health":
            self._json(200, health())
            return
        if path in ("/", "/index.html"):
            self._html(200, INDEX_HTML)
            return
        if path == "/v1/models":
            if not self._auth_ok():
                return
            self._json(200, openai_models())
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self._route()
        if path == "/api/v1/turn":
            self._turn()
            return
        if path == "/v1/chat/completions":
            self._chat_completions()
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def _read_json(self) -> dict | None:
        n = int(self.headers.get("content-length") or "0")
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "bad_json"})
            return None
        if not isinstance(payload, dict):
            self._json(400, {"ok": False, "error": "bad_json"})
            return None
        return payload

    def _turn(self) -> None:
        if not self._auth_ok():
            return
        payload = self._read_json()
        if payload is None:
            return
        message = str(payload.get("message") or "").strip()
        if not message:
            self._json(400, {"ok": False, "error": "empty_message"})
            return
        resolved, err = resolve_turn(payload)
        if err is not None:
            code = 400 if err.get("error") != "key_not_configured" else 503
            self._json(code, err)
            return
        assert resolved is not None
        result = run_hermes(message, resolved)
        if result.get("error") == "hermes_missing":
            self._json(503, {"ok": False, "error": "hermes_missing"})
            return
        if result.get("error") == "timeout":
            self._json(504, {"ok": False, "error": "timeout"})
            return
        self._json(
            200,
            {
                "ok": result["returncode"] == 0,
                "provider": result["provider"],
                "model": result["model"],
                "byok": result["byok"],
                "text": result["text"],
                "stderr_tail": result["stderr_tail"],
                "returncode": result["returncode"],
            },
        )

    def _chat_completions(self) -> None:
        if not self._auth_ok():
            return
        payload = self._read_json()
        if payload is None:
            return
        model_id = str(payload.get("model") or "").strip()
        pid, model = parse_openai_model(model_id)
        resolved, err = resolve_turn({"provider": pid, "model": model})
        if err is not None:
            code = 400 if err.get("error") != "key_not_configured" else 503
            self._json(code, {"error": {"message": err.get("error"), "type": "invalid_request_error"}})
            return
        assert resolved is not None
        prompt = messages_to_prompt(payload.get("messages"))
        if not prompt:
            self._json(400, {"error": {"message": "empty_message", "type": "invalid_request_error"}})
            return
        result = run_hermes(prompt, resolved)
        if result.get("error"):
            code = 504 if result["error"] == "timeout" else 503
            self._json(code, {"error": {"message": result["error"], "type": "server_error"}})
            return
        text = str(result.get("text") or "")
        if result.get("returncode") != 0:
            text = text or str(result.get("stderr_tail") or "hermes_failed")
        ctype, body = openai_completion(
            model_id or f"{pid}/{model}",
            text,
            bool(payload.get("stream")),
        )
        self._bytes(200, ctype, body)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Discovery Informatics · lab jail</title>
<style>
:root { color-scheme: light; --ink:#0d1117; --muted:#3a3f4a; --brand:#1a6b4a; --bg:#f5f4f0; }
body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--ink); }
main { max-width: 40rem; margin: 0 auto; padding: 3rem 1.25rem 4rem; }
h1 { font-size: 1.6rem; }
p, label { color: var(--muted); line-height: 1.55; }
textarea, input, select { width:100%; box-sizing:border-box; margin:.35rem 0 1rem; padding:.6rem; }
button { background:var(--brand); color:#fff; border:0; padding:.55rem 1rem; border-radius:999px; font-weight:600; }
pre { white-space:pre-wrap; background:#fff; padding:1rem; border:1px solid #dbd9d3; }
a { color: var(--brand); }
</style></head><body><main>
<p style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--brand)">Florida Man Bioscience</p>
<h1>Lab jail</h1>
<p>Generic Hermes lab profile (the class <code>yue-lab</code> belongs to). Empty desk. Bearer token required. Not a public unauthenticated agent.</p>
<p><a href="https://flmanbiosci.net/products/discovery-informatics">← Discovery Informatics</a></p>
<label>Shared token <input id="tok" type="password" autocomplete="off"/></label>
<label>Provider API key (optional — this turn only) <input id="apikey" type="password" autocomplete="off"/></label>
<label>Provider <select id="prov"></select></label>
<label>Model <select id="mod"></select></label>
<label>Ask <textarea id="msg" rows="4" placeholder="Normalize this public gene ID, then say cannots."></textarea></label>
<button type="button" id="go">Run turn</button>
<pre id="out"></pre>
<script>
const catalog = {};
fetch("/health").then(r => r.json()).then(h => {
  const sel = document.getElementById("prov");
  (h.providers || []).forEach(p => {
    catalog[p.id] = p;
    const o = document.createElement("option");
    o.value = p.id;
    o.textContent = p.label + (p.key_configured ? "" : " (bring your key)");
    sel.appendChild(o);
  });
  if (h.default_provider) sel.value = h.default_provider;
  fillModels();
});
function fillModels() {
  const p = catalog[document.getElementById("prov").value];
  const sel = document.getElementById("mod");
  sel.innerHTML = "";
  if (!p) return;
  p.models.forEach(m => {
    const o = document.createElement("option");
    o.value = m; o.textContent = m;
    if (m === p.default_model) o.selected = true;
    sel.appendChild(o);
  });
}
document.getElementById("prov").onchange = fillModels;
document.getElementById("go").onclick = async () => {
  const out = document.getElementById("out");
  out.textContent = "…";
  const body = {
    message: document.getElementById("msg").value,
    provider: document.getElementById("prov").value,
    model: document.getElementById("mod").value
  };
  const k = document.getElementById("apikey").value.trim();
  if (k) body.api_key = k;
  const r = await fetch("/api/v1/turn", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "authorization": "Bearer " + document.getElementById("tok").value
    },
    body: JSON.stringify(body)
  });
  out.textContent = await r.text();
};
</script>
</main></body></html>
"""


def main() -> None:
    Path(os.environ.get("HERMES_WORKSPACE", "/data/workspace")).mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"di-lab listening :{PORT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
