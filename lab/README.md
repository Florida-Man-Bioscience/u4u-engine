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
{"message":"…","provider":"openai","model":"gpt-4o"}
```

Allowlist: `neuralwatt`, `openai`, `openrouter`, `navigator`, `anthropic`, `xai`. Keys from env / `di-lab-keys` (`NEURALWATT_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `NAVIGATOR_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`). Do not put keys in git or the browser.

Never `--clone` yue-lab. Never bind host `$HOME`.

## theswamp (no iac)

Inventory lives here, not in `hwcopeland/iac`. Apply from this tree:

```bash
kubectl -n theswamp apply -f lab/k8s/theswamp.yaml
```

Public chat is **same-origin** on `/products/discovery-informatics#lab-console` via `/api/lab/*` → Service `di-lab:8080`. No HTTPRoute. No `lab.flmanbiosci.net`.
