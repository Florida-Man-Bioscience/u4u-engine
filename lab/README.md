# Generic lab jail (Discovery Informatics Wave 0.5)

Empty factory. **`yue-lab` is a tenant of this class**, not the image.

```bash
# local
docker build -t di-lab ./lab
docker run --rm -p 8080:8080 -e LAB_SHARED_TOKEN=dev di-lab
curl -sS localhost:8080/health
```

Never `--clone` yue-lab. Never bind host `$HOME`.
