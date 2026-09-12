# Generic lab jail (Discovery Informatics Wave 0.5)

Empty factory. **`yue-lab` is a tenant of this class**, not the image.

```bash
# local
docker build -t di-lab ./lab
docker run --rm -p 8080:8080 -e LAB_SHARED_TOKEN=dev di-lab
curl -sS localhost:8080/health
```

`GET /health` lists providers + `key_configured` (never the secret). `POST /api/v1/turn` body:

```json
{"message":"…","provider":"openai","model":"gpt-4o","api_key":"(optional BYOK)"}
```

Allowlist: `neuralwatt`, `openai`, `openrouter`, `navigator`, `anthropic`, `xai`. Jail keys from env / `di-lab-keys`. Optional per-turn `api_key` uses the visitor's key for that request only (not stored). Shared token is still required. Do not put keys in git.

Never `--clone` yue-lab. Never bind host `$HOME`.

## theswamp (no iac)

Inventory lives here, not in `hwcopeland/iac`. Apply from this tree:

```bash
kubectl -n theswamp apply -f lab/k8s/theswamp.yaml
```

Public chat is **same-origin** on `/products/discovery-informatics#lab-console` via `/api/lab/*` → Service `di-lab:8080`.

Open WebUI is at **https://flmanbiosci.net/owui** (Next.js rewrite → Service `lab-chat`, no new DNS). Apply the pod:

```bash
kubectl -n theswamp apply -f lab/k8s/open-webui.yaml
```

`WEBUI_AUTH=false`. Token stays in `di-lab-keys`. HTTPRoute is forbidden in this ns — do not add one.
