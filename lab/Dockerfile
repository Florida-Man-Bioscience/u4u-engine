FROM python:3.12-slim-bookworm

# Generic lab jail. Empty of partner trees. Hermes profile `lab` only.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HERMES_HOME=/data/profile \
    HERMES_WORKSPACE=/data/workspace \
    HERMES_PROFILE=lab \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

# Official install; fails closed if network is down at build.
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash \
    && ln -sf /root/.local/bin/hermes /usr/local/bin/hermes || true

WORKDIR /app
COPY server.py providers.py /app/
COPY profile/ /opt/lab-profile/

RUN mkdir -p /data/profile /data/workspace \
    && cp -a /opt/lab-profile/. /data/profile/ \
    && chmod -R a+rX /app /opt/lab-profile

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["python", "/app/server.py"]
