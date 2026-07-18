# ── Stage 1: build dependencies ───────────────────────────────────────────────
# pysam (VCF parsing) requires C build tools and several compression libraries.
# We install them here and discard the layer in the final image.
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-openssl-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy only what pip needs to install the engine package.
# engine/pyproject.toml uses where = [".."] so pip must run from /build (repo root).
COPY engine/ engine/
RUN pip install --no-cache-dir --prefix=/install "engine/[vcf]"

# Install FastAPI, uvicorn, Celery, Redis on top of the engine install.
# psycopg2-binary backs the Postgres pool in db/pool.py (loaded at import
# time even with the SQLite fallback active, so it must be present in
# the runtime image, not just the dev shell's flake.nix).
# pyjwt[crypto] is the same story: engine/users/token_validator.py does a
# module-level `import jwt`, which api.py pulls in via engine.users.deps —
# so a missing pyjwt is not a degraded feature, it crashes the app at import
# and the pod crash-loops. This list is hand-maintained and does NOT read
# requirements.txt, so anything imported at app-import time must be added here.
RUN pip install --no-cache-dir --prefix=/install \
    "fastapi>=0.110" \
    "uvicorn[standard]>=0.29" \
    "python-multipart>=0.0.9" \
    "celery>=5.3" \
    "redis>=5.0" \
    "reportlab>=4.1" \
    "sqlalchemy[asyncio]>=2.0" \
    "asyncpg>=0.29" \
    "pydantic>=2.6" \
    "psycopg2-binary>=2.9" \
    "pyjwt[crypto]>=2.8" \
    "cryptography>=42.0"


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime libraries needed by pysam + samtools + ExpansionHunter
RUN apt-get update && apt-get install -y --no-install-recommends \
    zlib1g \
    libbz2-1.0 \
    liblzma5 \
    libcurl4 \
    samtools \
    wget \
 && rm -rf /var/lib/apt/lists/*

# Install ExpansionHunter binary (v5.0.0, linux x86_64)
RUN wget -q https://github.com/Illumina/ExpansionHunter/releases/download/v5.0.0/ExpansionHunter-v5.0.0-linux_x86_64.tar.gz \
 && tar -xzf ExpansionHunter-v5.0.0-linux_x86_64.tar.gz \
 && mv ExpansionHunter-v5.0.0-linux_x86_64/bin/ExpansionHunter /usr/local/bin/ \
 && chmod +x /usr/local/bin/ExpansionHunter \
 && rm -rf ExpansionHunter-v5.0.0-linux_x86_64 ExpansionHunter-v5.0.0-linux_x86_64.tar.gz
ENV EXPANSION_HUNTER_PATH=/usr/local/bin/ExpansionHunter

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY engine/  engine/
COPY db/      db/
COPY scripts/ scripts/
COPY api.py   api.py

# Copy rsID filter files.
# data/ may be empty at build time — the pipeline handles missing filter files
# gracefully (treats them as empty sets). Populate before deploy or mount as a volume.
COPY data/ data/

# Run as non-root user — ensure data/ is writable for SQLite caches
RUN chmod +x /app/scripts/docker-entrypoint.sh \
 && useradd --no-create-home --shell /bin/false appuser \
 && chown -R appuser:appuser /app \
 && chmod 700 /app/data
USER appuser

# Expose the application port
EXPOSE 8000

# Liveness probe: container is healthy when /health returns 200
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start uvicorn.
# Hampton: set --workers to match CPU count on the K8s node.
# Gunicorn with uvicorn workers is an alternative for multi-process deployments:
#   ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
#   CMD ["gunicorn", "api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
#
# Set SEED_DEMO_DATA=1 to populate the biomarker tracking DB with synthetic
# patients/treatments/measurements on first start. The seeder is idempotent —
# it skips on container restart when patients already exist.
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
