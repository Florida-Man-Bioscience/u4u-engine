# Deploying the engine

This guide covers deploying the Florida Man Bioscience tracking stack
(tracking app + API) as two Docker containers. A TLS-terminating
reverse proxy in front of them is **out of scope for this repo** — it's
managed separately on the VPS (Caddy, nginx, Cloudflare Tunnel, etc.).

The deploy contract the external proxy must satisfy:

| Public URL                                 | Container          |
|--------------------------------------------|--------------------|
| `https://flmanbiosci.net/`                 | `frontend:3000`    |
| `https://flmanbiosci.net/api/v1/<path>`    | `api:8000/<path>`  |

That is: route `/api/v1/*` to the api container with the `/api/v1`
prefix stripped (because the backend routes live at `/tracking/*`,
`/jobs/*`, `/regulatory/*` — not under `/api/v1`). Everything else
goes to the frontend.

---

## 1. Provision a VPS

Any 2 GB / 1 vCPU box is plenty at our current scale. Ubuntu 24.04 LTS
is the easiest baseline. Open whatever ports your external proxy
needs (typically `22`, `80`, `443`).

## 2. Install Docker

```sh
ssh root@your.vps.ip
apt update && apt install -y docker.io docker-compose-v2 git
systemctl enable --now docker
```

## 3. Clone the repo

```sh
mkdir -p /opt/fmb && cd /opt/fmb
git clone https://github.com/Florida-Man-Bioscience/u4u-engine.git
```

## 4. Configure the environment

```sh
cd /opt/fmb/u4u-engine
cp .env.example .env
$EDITOR .env
```

Minimum production settings:

```
NCBI_API_KEY=<your NCBI key>
JOB_STORE_KEY=<output of python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'>

# Same-origin path: the external proxy at flmanbiosci.net forwards
# /api/v1/* to the api container.
NEXT_PUBLIC_API_BASE=/api/v1
```

The API has no authentication — every endpoint is open. Treat the
deploy as public; anything sensitive must be gated by the external
proxy (network ACL, basic auth, etc.).

## 5. Bring it up

```sh
cd /opt/fmb/u4u-engine
docker compose up -d --build
```

The api binds host port `8000` and the frontend binds `3000` — that's
what the external proxy talks to.

Verify the containers are healthy:

```sh
curl -I http://localhost:8000/health      # api on the box
curl -I http://localhost:3000/            # frontend on the box
```

The proxy team then verifies public reachability:

```sh
curl -I https://flmanbiosci.net/                    # → frontend:3000
curl -I https://flmanbiosci.net/api/v1/health       # → api:8000/health
```

## 6. Updates

Pull and rebuild:

```sh
cd /opt/fmb/u4u-engine && git pull
docker compose up -d --build
```

---

## Local development

The compose file works locally with no env changes:

```sh
docker compose up --build
# http://localhost:3000           → frontend
# http://localhost:8000           → api
# http://localhost:8000/health    → liveness check
```

The frontend builds with `NEXT_PUBLIC_API_BASE=http://localhost:8000`
by default (the compose-level fallback), so direct `:3000` access
works without any proxy in the picture.
