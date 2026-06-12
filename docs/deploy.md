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
prefix stripped (because the backend routes live at `/auth/*`,
`/tracking/*`, `/jobs/*` — not under `/api/v1`). Everything else goes
to the frontend.

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
API_KEYS=<long random string>
AUTH_BOOTSTRAP_USERNAME=<admin user>
AUTH_BOOTSTRAP_PASSWORD=<initial admin password>
JOB_STORE_KEY=<output of python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'>

# Same-origin path: the external proxy at flmanbiosci.net forwards
# /api/v1/* to the api container.
NEXT_PUBLIC_API_BASE=/api/v1
```

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

## 5a. Authentication model

The API has two parallel auth mechanisms; either grants access to every
protected endpoint.

**Session tokens** (intended for human users via the web UI):
- `AUTH_BOOTSTRAP_USERNAME` + `AUTH_BOOTSTRAP_PASSWORD` seed a single
  admin account the first time the API starts against an empty
  `data/auth.db`. **Editing these env vars later does NOT rotate the
  password** — by design, so anyone with deploy access can't silently
  take over a live account.
- The user signs in at `https://flmanbiosci.net/login`, the frontend
  stores the returned bearer token in `localStorage`, and every API
  call afterwards attaches it as `Authorization: Bearer …`.
- Tokens last 7 days (override with `AUTH_SESSION_TTL_DAYS`).
- `/auth/login` is rate-limited at 10 attempts per 5 minutes per IP
  (via `X-Forwarded-For` from the proxy). Hitting the limit returns
  429 with a `Retry-After` header.
- To change the password, the operator signs in and visits
  `https://flmanbiosci.net/account`. The change revokes every active
  session for the user; the page automatically swaps in the
  freshly-minted token so the operator stays signed in.
- Lost password recovery: stop the api container, delete
  `data/auth.db`, restart. The bootstrap will re-seed using the
  current env values. Any active sessions are lost.

**API keys** (intended for service-to-service calls):
- `API_KEYS=k1,k2,…` accepts either header form:
  `Authorization: Bearer k1` or `X-API-Key: k1`.
- API-key callers have no user context — `/auth/me` returns the
  `via: "api_key"` sentinel and `/auth/password` refuses them with 403.

**Fail-closed semantics:**
- With neither `API_KEYS` set nor any users in the DB, protected
  endpoints return **503** ("Authentication is not configured on this
  server"). This is the truthful response: there is no way to
  authenticate, so the server can't accept anyone.
- With users (or keys) present but no/bad credentials on the request,
  endpoints return **401**.
- For local development only, `ALLOW_INSECURE_NO_AUTH=1` skips the
  middleware. Never set this in production.

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
