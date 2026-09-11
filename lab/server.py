"""Thin HTTP front for the generic Hermes lab profile.

GET  /health          — probes (no secrets)
GET  /                — gated chat HTML
POST /api/v1/turn     — Bearer LAB_SHARED_TOKEN required
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("PORT", "8080"))
PROFILE = os.environ.get("HERMES_PROFILE", "lab")
TOKEN = os.environ.get("LAB_SHARED_TOKEN", "")
TURN_TIMEOUT = int(os.environ.get("LAB_TURN_TIMEOUT", "120"))


def health() -> dict:
    return {
        "ok": True,
        "profile": PROFILE,
        "product": "discovery-informatics",
        "class": "lab-jail",
        "token_configured": bool(TOKEN),
        "workspace": os.environ.get("HERMES_WORKSPACE", "/data/workspace"),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

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

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/health":
            self._json(200, health())
            return
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            self._html(200, INDEX_HTML)
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/v1/turn":
            self._json(404, {"ok": False, "error": "not_found"})
            return
        if not TOKEN:
            self._json(503, {"ok": False, "error": "token_not_configured"})
            return
        auth = self.headers.get("Authorization", "")
        got = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if got != TOKEN:
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        n = int(self.headers.get("content-length") or "0")
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "bad_json"})
            return
        message = str(payload.get("message") or "").strip()
        if not message:
            self._json(400, {"ok": False, "error": "empty_message"})
            return
        hermes = os.environ.get("HERMES_BIN", "hermes")
        cmd = [hermes]
        if PROFILE and PROFILE not in ("default", "-"):
            cmd += ["-p", PROFILE]
        cmd += ["chat", "-q", message, "-Q"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TURN_TIMEOUT,
                cwd=os.environ.get("HERMES_WORKSPACE", "/data/workspace"),
                env={**os.environ, "HERMES_HOME": os.environ.get("HERMES_HOME", "/data/profile")},
            )
        except FileNotFoundError:
            self._json(503, {"ok": False, "error": "hermes_missing"})
            return
        except subprocess.TimeoutExpired:
            self._json(504, {"ok": False, "error": "timeout"})
            return
        self._json(
            200 if proc.returncode == 0 else 502,
            {
                "ok": proc.returncode == 0,
                "text": (proc.stdout or "")[-12000:],
                "stderr_tail": (proc.stderr or "")[-2000:],
                "returncode": proc.returncode,
            },
        )


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
textarea, input { width:100%; box-sizing:border-box; margin:.35rem 0 1rem; padding:.6rem; }
button { background:var(--brand); color:#fff; border:0; padding:.55rem 1rem; border-radius:999px; font-weight:600; }
pre { white-space:pre-wrap; background:#fff; padding:1rem; border:1px solid #dbd9d3; }
a { color: var(--brand); }
</style></head><body><main>
<p style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--brand)">Florida Man Bioscience</p>
<h1>Lab jail</h1>
<p>Generic Hermes lab profile (the class <code>yue-lab</code> belongs to). Empty desk. Bearer token required. Not a public unauthenticated agent.</p>
<p><a href="https://flmanbiosci.net/products/discovery-informatics">← Discovery Informatics</a></p>
<label>Token <input id="tok" type="password" autocomplete="off"/></label>
<label>Ask <textarea id="msg" rows="4" placeholder="Normalize this public gene ID, then say cannots."></textarea></label>
<button type="button" id="go">Run turn</button>
<pre id="out"></pre>
<script>
document.getElementById('go').onclick = async () => {
  const out = document.getElementById('out');
  out.textContent = '…';
  const r = await fetch('/api/v1/turn', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'authorization': 'Bearer ' + document.getElementById('tok').value
    },
    body: JSON.stringify({ message: document.getElementById('msg').value })
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
