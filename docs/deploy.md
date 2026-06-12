# Deploying the engine on a VPS

This guide walks through deploying the Florida Man Bioscience tracking
stack (tracking app + API + reverse proxy) on a single Linux VPS.

URL layout produced by this setup:

| URL                                       | Service                            |
|-------------------------------------------|------------------------------------|
| `https://flmanbiosci.net/`                | tracking app (Next.js frontend)    |
| `https://www.flmanbiosci.net/`            | 301 → `https://flmanbiosci.net/`   |
| `https://flmanbiosci.net/api/v1/...`      | FastAPI                            |

TLS is auto-managed by Caddy via Let's Encrypt.

---

## 1. Provision a VPS

Any 2 GB / 1 vCPU box is plenty at our current scale (Hetzner CX22 ~€4/mo,
DigitalOcean basic $6/mo, Linode Nanode $5/mo, etc.). Ubuntu 24.04 LTS is the
easiest baseline.

Open firewall ports `22`, `80`, `443` to the public internet.

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

SITE_ADDRESS=flmanbiosci.net, www.flmanbiosci.net
NEXT_PUBLIC_API_BASE=/api/v1
```

## 5. Point Cloudflare DNS at the box

In the Cloudflare dashboard for `flmanbiosci.net`:

| Type | Name | Value         | Proxy status |
|------|------|---------------|--------------|
| A    | `@`  | `<vps.ip>`    | **DNS only** |
| A    | `www`| `<vps.ip>`    | **DNS only** |

`DNS only` (grey cloud) is required so Caddy can complete the HTTP-01 ACME
challenge directly. Once Let's Encrypt has issued certs you can switch
Cloudflare back to proxied mode if you want CF in front, but then you must
also install a Cloudflare Origin Certificate on the VPS (Caddy can serve it
from the `tls` directive) — or use the DNS-01 challenge with a Cloudflare API
token (requires a Caddy build that includes the Cloudflare DNS module).

## 6. Bring it up

```sh
cd /opt/fmb/u4u-engine
docker compose up -d --build
docker compose logs -f proxy   # watch Caddy fetch certs
```

Verify:

```sh
curl -I https://flmanbiosci.net/                       # tracking app
curl -I https://flmanbiosci.net/api/v1/health          # api
```

## 6a. Authentication model

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
  (via `X-Forwarded-For` from Caddy). Hitting the limit returns 429
  with a `Retry-After` header.
- To change the password, the operator signs in and visits
  `https://flmanbiosci.net/account`. The change revokes every
  active session for the user; the page automatically swaps in the
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

## 7. Updates

Pull and rebuild the changed service:

```sh
cd /opt/fmb/u4u-engine && git pull
docker compose up -d --build
```

For zero-downtime rollouts later, swap to a CI/CD push from the GHA
workflow.

---

## Local development

The same compose file works locally with no env changes:

```sh
docker compose up --build
# http://localhost                  → tracking app (via Caddy)
# http://localhost/api/v1/health    → api (via Caddy)
# http://localhost:8000             → api (direct, bypassing proxy)
# http://localhost:3000             → frontend (direct, bypassing proxy)
```

The direct port mappings are preserved so you can hit any service without
going through Caddy when debugging.
