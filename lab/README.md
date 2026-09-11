# Generic lab jail (Discovery Informatics Wave 0.5)

Empty factory. **`yue-lab` is a tenant of this class**, not the image.

```bash
# local
docker build -t di-lab ./lab
docker run --rm -p 8080:8080 -e LAB_SHARED_TOKEN=dev di-lab
curl -sS localhost:8080/health
```

Never `--clone` yue-lab. Never bind host `$HOME`.

## theswamp (no iac)

Inventory lives here, not in `hwcopeland/iac`. Apply from this tree:

```bash
kubectl -n theswamp apply -f lab/k8s/theswamp.yaml
```

Public chat is **same-origin** on `/products/discovery-informatics#lab-console` via `/api/lab/*` → Service `di-lab:8080`. No HTTPRoute. No `lab.flmanbiosci.net`.
