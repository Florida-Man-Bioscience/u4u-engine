# Server management & production deployment (hwcopeland cluster)

This is the operations runbook for the **production** deployment of u4u-engine,
which runs on the self-hosted **hwcopeland homelab Kubernetes cluster**, not on a
standalone VPS. If you are debugging "why isn't my change live" or "why won't the
pod start," start here.

> **Two deployment paths — don't confuse them.**
> - **Production (this doc):** RKE2 Kubernetes + Flux GitOps on the hwcopeland
>   cluster, serving `https://flmanbiosci.net`. Releases are automatic on push to
>   `main`. No manual `kubectl apply` for normal releases.
> - **Standalone single-host:** the Docker-Compose-on-a-VPS flow in
>   [`deploy.md`](./deploy.md). Self-contained; useful for a throwaway/demo box or
>   local-prod parity. It is *not* what serves flmanbiosci.net.

## Source of truth: the `hwcopeland/iac` repository

All cluster/server config lives in **<https://github.com/hwcopeland/iac>**
("Infrastructure as Code for Homelab Automation"). It is cloned locally at
`../iac` (i.e. `/home/noahtjones/iac`).

The pieces that own *our* app:

| Path in `hwcopeland/iac` | What it defines |
|---|---|
| `rke2/tooling/flux/theswamp/` | Our namespace's manifests: Deployments, Services, HTTPRoutes, Postgres, RBAC, pull/DB secrets |
| `rke2/tooling/flux/image-automation/` | Flux ImageRepository / ImagePolicy / ImageUpdateAutomation that auto-roll new images |
| `rke2/tooling/flux/theswamp/ACCESS.md` | How an FMB collaborator gets `kubectl` access to `theswamp` |
| `CLAUDE.md` (in iac root) | Authoritative cluster overview (nodes, namespaces, networking, secrets, CI) |

> ⚠️ **`hwcopeland/iac/docs/TROUBLESHOOTING.md` and `docs/rke2/README.md` are
> stale.** They describe **Canal CNI, MetalLB, nginx-ingress, and ArgoCD** — none
> of which this cluster uses anymore. The current stack is **Cilium CNI/Gateway +
> Flux GitOps**. Trust `iac/CLAUDE.md` and the live manifests, not those older docs.

## Production topology

```
Internet
  → Cloudflare (proxied DNS for flmanbiosci.net)
  → Cilium Gateway  (hwcopeland-gateway, kube-system, IP 10.44.0.1, HTTPS:443)
  → HTTPRoute (theswamp/u4u-engine)
       /api/v1/*  → Service u4u-engine          → Deployment u4u-engine (api, :8000)   [/api/v1 prefix stripped]
       /*         → Service u4u-engine-frontend  → Deployment u4u-engine-frontend (:3000)
  → Deployment talks to → StatefulSet u4u-postgres (:5432, headless svc)
```

- **Namespace:** `theswamp`
- **Public URL:** `https://flmanbiosci.net` (and `www.` → 301 redirect to apex)
- **Container registry:** `zot.hwcopeland.net/florida-man-bioscience/` (internal Zot, OCI)
- **Images:** `u4u-engine` (api, port 8000) and `u4u-engine-frontend` (port 3000)
- **Database:** in-cluster `postgres:16-alpine` StatefulSet, 10Gi Longhorn PVC,
  DNS `u4u-postgres.theswamp.svc.cluster.local:5432`, db/user `u4u`
- **Secrets:** External Secrets Operator pulls from Bitwarden (Vaultwarden) via the
  `bitwarden-login` ClusterSecretStore
- **TLS:** wildcard cert managed by cert-manager on the gateway

## How a release actually ships (the GitOps loop)

There is **no manual deploy step** for a normal change. Pushing to `main` triggers
this chain:

1. **CI builds the image.** `.github/workflows/build-and-push.yml` (api) and
   `build-and-push-frontend.yml` (frontend) run on a **self-hosted runner on the
   hwcopeland server** (`runs-on: [self-hosted, hwcopeland]`). They build the
   Docker image and push it to `zot.hwcopeland.net/florida-man-bioscience/u4u-engine`
   (and `-frontend`), tagged `main` plus a short-SHA tag.
   - The frontend build only fires on changes under `frontend/**`, and bakes
     `NEXT_PUBLIC_API_BASE` in at build time (from a CI secret).
2. **Flux notices the new digest.** `ImageRepository` scans Zot every 1m;
   `ImagePolicy` tracks the `^main$` tag with `digestReflectionPolicy: Always`, so a
   *new image behind the same `main` tag* still counts as an update.
3. **Flux rewrites the manifest and commits it.** `ImageUpdateAutomation` updates the
   pinned digest in `rke2/tooling/flux/theswamp/deployment.yaml` (and
   `deployment-frontend.yaml`) via the `# {"$imagepolicy": "tooling:u4u-engine"}`
   setter comment, then commits to `iac` `main` as `fluxcdbot`
   (`[ci skip] auto-update u4u-engine`).
4. **Flux rolls out the new pod.** The kustomization in `theswamp/` reconciles the new
   digest and Kubernetes does a rolling update.

> 🔒 **Never delete or reformat the `# {"$imagepolicy": ...}` comments** in
> `deployment.yaml` / `deployment-frontend.yaml`. They are Flux setter markers; without
> them the SHA pin stops auto-updating and releases silently stop shipping.

**Implication:** Flux only ever deploys what is committed to **`origin/main` of
`hwcopeland/iac`**. A manifest sitting uncommitted in someone's local `iac` working
tree is invisible to the cluster. This is the #1 source of "I changed it but nothing
happened" (see below).

## Deployment failure-mode map

Work top-down; the first two are the live suspects as of this writing.

### 1. Manifest changes never deployed → they're not on `origin/main`
Flux reconciles `origin/main`, not your laptop. Check what's actually shipped vs. local:
```sh
cd ../iac
git fetch
git status -s rke2/tooling/flux/theswamp/      # ?? = untracked, M = modified-not-pushed
git log origin/main --oneline -- rke2/tooling/flux/theswamp/<file>.yaml   # empty = never pushed
git show origin/main:rke2/tooling/flux/theswamp/kustomization.yaml        # is the file even listed?
```
If a manifest is `??`/`M`, or absent from the committed `kustomization.yaml`, the
cluster has never seen it. Fix = commit + push it to `iac` `main` (then let Flux
reconcile, or `flux reconcile kustomization theswamp`).

> **Known live gotcha (DB layer not shipped):** `postgres.yaml` (the Postgres
> StatefulSet + Service + `u4u-postgres-secret` ExternalSecret) and the
> `deployment.yaml` change that injects `DATABASE_URL` have been observed
> **uncommitted** in the local `iac` tree, and the committed `kustomization.yaml`
> does **not** list `postgres.yaml`. Result: the live pod runs with **no database
> wiring at all**, and applying the local edits as-is would fail at step 2 below.
> If u4u-engine's DB features are "not working in prod," verify this first.

### 2. Pod stuck / `CreateContainerConfigError` → the Postgres secret never resolved
`deployment.yaml` injects `DATABASE_URL` from secret `u4u-postgres-secret`, which is
*created by* the ExternalSecret in `postgres.yaml`. That ExternalSecret currently has
a placeholder Bitwarden key:
```yaml
remoteRef:
  key: REPLACE_WITH_BITWARDEN_ITEM_UUID   # <-- must be a real Bitwarden item UUID
```
Until a real UUID is filled in (create a Bitwarden Login item `u4u` / strong password,
paste its UUID), the ExternalSecret stays unready → `u4u-postgres-secret` is never
created → the api pod can't mount `DATABASE_URL` and won't start. Diagnose:
```sh
kubectl -n theswamp get externalsecret
kubectl -n theswamp describe externalsecret u4u-postgres-secret
kubectl -n theswamp get secret u4u-postgres-secret        # missing = not resolved
```

### 3. `ImagePullBackOff` → registry pull secret
Pods pull from the private Zot registry using `imagePullSecrets: zot-pull-secret`,
itself an ExternalSecret (`zot-pull-secret.yaml`) backed by Bitwarden. Diagnose:
```sh
kubectl -n theswamp describe pod <pod>           # look at Events
kubectl -n theswamp get secret zot-pull-secret
```

### 4. New image built but pod not updating → Flux image automation
```sh
flux get image repository u4u-engine -n tooling      # last scan, errors
flux get image policy     u4u-engine -n tooling      # what digest it selected
flux get image update     u4u-engine -n tooling      # last commit it pushed
```
If the policy isn't advancing: confirm CI actually pushed a new digest to Zot, and that
the `$imagepolicy` setter comment is intact in `deployment.yaml`.

### 5. CI never ran → self-hosted runner offline
Both build workflows require a runner labeled `[self-hosted, hwcopeland]`. If that
runner (the `arc-chem` ARC runner in the cluster) is down, builds queue forever and no
image is pushed. Check GitHub Actions run status and the runner in `arc-system`.

### 6. 404 / wrong-service routing → HTTPRoute / Gateway
The route attaches to the gateway via `parentRefs ... sectionName`. The main route uses
`sectionName: flmanbiosci-root-https` (exact apex); the `www` redirect uses
`flmanbiosci-https` (wildcard listener). A `sectionName` that doesn't match a real
gateway listener means the route silently doesn't attach.
```sh
kubectl -n theswamp describe httproute u4u-engine     # check Parents/Accepted conditions
kubectl -n kube-system get gateway hwcopeland-gateway -o yaml | grep -A2 'name:'   # listener names
```
Remember the rewrite: `/api/v1/*` is **prefix-stripped to `/`** before hitting the api
(backend routes live at `/tracking/*`, `/jobs/*`, `/regulatory/*`).

### 7. Generic pod debugging
```sh
kubectl -n theswamp get pods
kubectl -n theswamp logs deploy/u4u-engine
kubectl -n theswamp logs deploy/u4u-engine --previous     # last crash
kubectl -n theswamp get events --sort-by=.lastTimestamp
kubectl -n theswamp rollout status deploy/u4u-engine
```
Note resource limits: api pod is capped at `4Gi`/`500m` — a memory-heavy analysis run
can get OOM-killed (shows as `Last State: OOMKilled`).

## Getting cluster access (`theswamp` only)

FMB collaborators (`jonesnoaht`, `curtisdearing`) get **namespace-admin in `theswamp`
and nothing else** (RBAC in `theswamp/rbac.yaml`). Full details in
`../iac/rke2/tooling/flux/theswamp/ACCESS.md`. Two options:

- **A — Static API key (simplest, no browser).** An admin mints a `swamp-dev`
  ServiceAccount token and hands you a kubeconfig:
  ```sh
  kubectl -n theswamp create token swamp-dev --duration=2160h   # 90 days
  ```
  You then `KUBECONFIG=swamp.kubeconfig kubectl get pods -n theswamp`. Works only in
  `theswamp`; any verb elsewhere is denied.
- **B — Per-user SSO (OIDC, auditable).** Members of the Authentik "Florida Man
  Bioscience" group authenticate as themselves via `kubelogin` against
  `auth.hwcopeland.net`. Use this for per-person attribution.

> **Reachability:** RBAC grants permission, not network path — the kube-apiserver must
> be reachable from where you run `kubectl` (home LAN / VPN).

## Monitoring access — the Grafana "Swamp" dashboard

FMB collaborators watch tooling/genomics health through a dedicated **"Swamp"**
folder in Grafana at **<https://grafana.hwcopeland.net>**. Full operator runbook:
`../iac/rke2/chem/khemeia/docs/swamp-management-runbook.md`.

**What FMB membership actually grants (least-privilege — state it plainly):**
- **Editor** org-role in Grafana + **Admin** on the *Swamp folder only* → manage
  dashboards/alerts within Swamp, touch nothing else.
- Interactive **Khemeia web** login (browse jobs/results) via GitHub → Authentik.
- It is **not** API-level admin over genome jobs, and does **not** grant the ability
  to rotate the u4u API token — those stay with the platform owner by design.

**How access is wired:**
- Membership is the Authentik group **"Florida Man Bioscience"** (pinned UUID
  `5f7efde0-fe9b-48f1-b443-e42947bf7f2e`). The group → `Editor` org-role mapping is
  declarative (in `iac`), so no click-ops for the role itself.
- **Admin on the Swamp folder is a one-time manual grant** — folder-scoped perms
  can't come from an OIDC claim. A GrafanaAdmin sets it once via
  Grafana → Dashboards → Folders → **Swamp** → Permissions → add role **Editor** =
  **Admin**.

**Onboarding a new collaborator (e.g. Curtis / Tom):**
1. They sign up at grafana.hwcopeland.net or khemeia.net with **"Sign up with
   GitHub"** → account is created **inactive** (pending approval).
2. The owner **activates** them in Authentik (Directory → Users → Active) and notes
   their exact Authentik **username**.
3. Add that username to the FMB group's `users:` list — **in both**
   `rke2/authentik/blueprints/groups.yaml` **and** the mirrored `groups.yaml` key in
   `rke2/authentik/blueprints-configmap.yaml` (the ConfigMap is what Authentik
   actually mounts; `update.sh` is only a `helm upgrade`, not a blueprint generator —
   editing only one file silently drops the change).
4. Apply: commit both, then `cd rke2/authentik && ./update.sh` (or let Flux
   reconcile). No pod restart needed; blueprints reconcile on a timer.
5. Verify: the user's Grafana **Org role** reads **Editor** and they can manage the
   Swamp folder.

> The empty group blocks nothing — the dashboard, role mapping, and folder all exist
> regardless. Don't invent usernames before someone actually enrolls.

## Quick reference

```sh
# everything in our namespace
kubectl -n theswamp get all

# tail the api / frontend
kubectl -n theswamp logs -f deploy/u4u-engine
kubectl -n theswamp logs -f deploy/u4u-engine-frontend

# force a fresh pull + restart (e.g. after a manual image change)
kubectl -n theswamp rollout restart deploy/u4u-engine

# Flux state for our images
flux get image all -n tooling

# nudge Flux to reconcile now instead of waiting for the interval
flux reconcile kustomization theswamp --with-source
```
