# Generic lab jail (Discovery Informatics Wave 0.5)

Empty factory. **`yue-lab` is a tenant of this class**, not the image.

```bash
# local
docker build -t di-lab ./lab
docker run --rm -p 8080:8080 -e LAB_SHARED_TOKEN=dev di-lab
curl -sS localhost:8080/health
```

`GET /health` lists providers + `key_configured` (never the secret). `POST /api/v1/turn` body (one-shot `message` still works; prefer `messages` for a thread):

```json
{"message":"…","messages":[{"role":"user","content":"…"},{"role":"assistant","content":"…"},{"role":"user","content":"follow-up"}],"provider":"openai","model":"gpt-4o","api_key":"(optional BYOK)"}
```

Each Hermes turn preloads skill `lit-review` (`LAB_PRELOAD_SKILLS`, comma-separated). Engine is `/opt/litreview`.


Allowlist: `neuralwatt`, `openai`, `openrouter`, `navigator`, `anthropic`, `xai`. Jail keys from env / `di-lab-keys`. Optional per-turn `api_key` uses the visitor's key for that request only (not stored). Shared token is still required. Do not put keys in git.

Never `--clone` yue-lab. Never bind host `$HOME`.

## theswamp (no iac)

Inventory lives here, not in `hwcopeland/iac`. Apply from this tree:

```bash
kubectl -n theswamp apply -f lab/k8s/theswamp.yaml
```

Paper-decomposition engine is `/opt/litreview` (`ENGINE_VERSION` on `GET /health` → `tools[]`). Admit JSONL:

```bash
curl -sS -H "Authorization: Bearer $LAB_SHARED_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"jsonl":"..."}' \
  http://di-lab:8080/api/v1/tools/paper-decomposition/admit
```

Same-origin from the apex console: `POST /api/lab/tools/paper-decomposition/admit`.

Public UI is **same-origin** on `/products/discovery-informatics#lab-console` via `/api/lab/*` → Service `di-lab:8080`. The console is **multi-shot** (thread in the page; POST `messages[]`). Open WebUI on a dedicated host still waits on IAC.

Open WebUI Deployment `lab-chat` serves at **`/`** on ClusterIP `:8080` (unmodified image, no `/owui` rewrite). Public hostname `lab-chat.flmanbiosci.net` needs the IAC HTTPRoute+DNSRecord in `lab/k8s/iac-httproute-lab-chat.yaml` — Noah opens that PR; do not kubectl-apply HTTPRoutes from this identity.

```bash
kubectl -n theswamp apply -f lab/k8s/open-webui.yaml
```

Token stays in `di-lab-keys`. `/owui` on the apex site redirects to the console.
