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

Open WebUI (NaviGator-like) is a **separate pod**. You PR IAC; apply the app here:

```bash
# 1. You: copy lab/k8s/iac-httproute-lab-chat.yaml →
#    iac/rke2/tooling/flux/theswamp/httproute-lab-chat.yaml
#    and add `- httproute-lab-chat.yaml` to that kustomization.yaml.
# 2. After di-lab image with /v1/chat/completions is live:
kubectl -n theswamp apply -f lab/k8s/open-webui.yaml
```

Open WebUI uses `OPENAI_API_BASE_URL=http://di-lab:8080/v1` and `OPENAI_API_KEY` = `LAB_SHARED_TOKEN` from `di-lab-keys` (not in git). `WEBUI_AUTH=false`.
