# Deploying the engine (standalone single-host)

> **Scope:** this is the **standalone Docker-Compose-on-a-VPS** path — a
> self-contained box you provision and run yourself. It is **not** how
> `flmanbiosci.net` is served. Production runs on the self-hosted hwcopeland
> RKE2/Kubernetes cluster with Flux GitOps — see
> [`server-management.md`](./server-management.md) for that, and for deployment
> troubleshooting.

This guide covers deploying the Florida Man Bioscience tracking stack
(tracking app + API) as three Docker[^docker] containers: `api`, `frontend`,
and a bundled `postgres`[^postgres] service. A TLS-terminating[^tls]
reverse proxy[^revproxy] in front of them is **out of scope for this repo** — it's
managed separately on the VPS[^vps] (Caddy, nginx, Cloudflare Tunnel, etc.).[^proxies]

The compose file brings up a `postgres:16-alpine` service and wires
`DATABASE_URL` into the api container automatically, so the engine uses
Postgres for the annotation cache, rsID cache, biomarker tracking, jobs,
and HealthKit ingestion. It auto-migrates on startup (`db/migrate.py`).
Postgres is an **internal** service — only `api` and `frontend` are
public-facing, so the external proxy contract is unchanged.

The deploy contract the external proxy must satisfy:

| Public URL                                 | Container          |
|--------------------------------------------|--------------------|
| `https://flmanbiosci.net/`                 | `frontend:3000`    |
| `https://flmanbiosci.net/api/v1/<path>`    | `api:8000/<path>`  |

That is: route `/api/v1/*` to the api container with the `/api/v1`
prefix stripped (because the backend routes live at `/tracking/*`,
`/jobs/*`, `/healthkit/*`, `/regulatory/*` — not under `/api/v1`).
Everything else goes to the frontend.

---

## 1. Provision a VPS

Any 2 GB / 1 vCPU[^vcpu] box is plenty at our current scale. Ubuntu 24.04 LTS[^lts]
is the easiest baseline. Open whatever ports your external proxy
needs (typically `22`, `80`, `443`).[^ports]

## 2. Install Docker

```sh
ssh root@your.vps.ip
apt update && apt install -y docker.io docker-compose-v2 git
systemctl enable --now docker
```

This installs Docker and enables it as a service via `systemctl`[^systemctl] (the systemd service manager), so the daemon starts on boot.

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

# Same-origin path: the external proxy at flmanbiosci.net forwards
# /api/v1/* to the api container.
NEXT_PUBLIC_API_BASE=/api/v1
```

You usually do **not** set `DATABASE_URL` here: the compose file ships a
`postgres` service and wires `DATABASE_URL` to it automatically. Set it
only to point the api at a *different* database (an external/managed
Postgres). When `DATABASE_URL` is unset entirely, the engine falls back
to local SQLite files under `data/` and jobs live in memory only.

> **`JOB_STORE_KEY` is deprecated and ignored.** Jobs now persist to
> Postgres when `DATABASE_URL` is set (in-memory otherwise); the old
> Fernet-encrypted on-disk job snapshot has been removed. Setting the
> variable does nothing but log a deprecation warning.

**Harden the bundled Postgres for a real deployment.** The compose
`postgres` service ships with a **dev-only** password
(`POSTGRES_PASSWORD: u4u_dev_password`) and publishes `5432` on the host —
fine for local development, not for a public VPS. Before going live:

- Override the password to a strong secret and update the matching
  `DATABASE_URL` credentials (both must agree — the api authenticates to
  Postgres with them).
- Do **not** expose port `5432` publicly; remove the `postgres` host
  port mapping or firewall the port so only the `api` container reaches it.

### Authentication

The API is **mostly** unauthenticated: the analysis (`/analyze`,
`/jobs/*`), tracking (`/tracking/*`), and regulatory (`/regulatory/*`)
endpoints have no auth. The exception is **HealthKit ingestion**
(`POST`/`GET /healthkit/samples`), which requires a per-device bearer
token (`engine/healthkit/auth.py`). This check is **fail-closed whenever
`DATABASE_URL` is set** — which is the case for this compose deploy — so
in production a valid device token is *always* required to write or read
HealthKit samples and no env var can turn it off. Mint tokens with
`scripts/create_healthkit_token.py`.

Everything else stays open, so treat the deploy as public: anything
sensitive on the open endpoints must be gated by the external proxy
(network ACL[^acl], basic auth[^basicauth], etc.).

## 5. Bring it up

```sh
cd /opt/fmb/u4u-engine
docker compose up -d --build
```

The api binds host port `8000` and the frontend binds `3000` — that's
what the external proxy talks to. The `postgres` service starts first;
the api waits for it to pass its health check (`pg_isready`) before
booting and running migrations.

Verify the containers are healthy:

```sh
docker compose ps                         # all three services Up (postgres healthy)
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
works without any proxy in the picture. (`/health` is a liveness check[^liveness] —
a lightweight endpoint a proxy or orchestrator polls to confirm the service is up.)

---

## Footnotes

[^docker]: **Docker** — a containerization platform that packages an app and its dependencies into an isolated, reproducible image that runs the same anywhere. `docker compose` runs multiple containers together from one config file.
[^tls]: **TLS-terminating** — the proxy handles the HTTPS/TLS encryption layer (certificates, decryption) so the backend containers can speak plain HTTP internally. TLS is the protocol behind `https://`.
[^revproxy]: **Reverse proxy** — a server that sits in front of backend services, receives client requests, and forwards them to the right container; also handles TLS, routing, and access control.
[^vps]: **VPS (Virtual Private Server)** — a rented virtual machine from a cloud/hosting provider, used as the deployment host.
[^proxies]: **Caddy / nginx / Cloudflare Tunnel** — interchangeable reverse-proxy options: Caddy (auto-HTTPS web server), nginx (high-performance web server/proxy), Cloudflare Tunnel (exposes a local service through Cloudflare without opening inbound ports).
[^vcpu]: **vCPU** — a virtual CPU core allocated to the VPS; "1 vCPU" is one such core's share of the physical host.
[^lts]: **LTS (Long-Term Support)** — an OS release (here Ubuntu 24.04) that receives security/maintenance updates for an extended period, preferred for servers.
[^ports]: **Ports 22 / 80 / 443** — standard TCP ports: 22 (SSH, remote shell), 80 (HTTP), 443 (HTTPS).
[^systemctl]: **systemctl** — the command-line interface to `systemd`, Linux's service/init manager; `enable --now` both starts a service and sets it to launch on boot.
[^postgres]: **Postgres** — PostgreSQL, the relational database the engine uses for its caches, biomarker tracking, jobs, and HealthKit data. The compose file bundles the official `postgres:16-alpine` image; production on the k8s cluster runs an in-cluster StatefulSet with a Bitwarden-sourced password.
[^acl]: **Network ACL (Access Control List)** — firewall-style rules that allow or deny traffic by source IP/port, restricting who can reach the service.
[^basicauth]: **Basic auth** — HTTP Basic Authentication, a simple username/password challenge sent with each request; here applied at the proxy to gate the otherwise-open API.
[^liveness]: **Liveness check** — a minimal endpoint (`/health`) that a proxy, load balancer, or orchestrator polls to verify the process is alive and able to serve requests.
