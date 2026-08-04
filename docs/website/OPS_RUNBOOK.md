# OPS runbook — flmanbiosci.net on hwcopeland / theswamp

**Audience:** operators and agents who must change or verify the public site without freestyling.  
**Plan:** Arete `p-01184334` (FMB website restructure) · task `t-fmbweb-ops-docs`  
**Canonical path in repo:** `docs/website/OPS_RUNBOOK.md`  
**This host worktree (when authored):** `/home/noahtjones/u4u-engine/.worktrees/t_af09bfbc`  
**No production cluster mutations from documentation tasks.**

---

## 1. Purpose

Operate **`https://flmanbiosci.net`** (and related hosts) on the **hwcopeland** homelab RKE2 cluster, namespace **`theswamp`**, using **Flux GitOps** — not ad-hoc `kubectl apply`, not Vercel/Netlify, not the standalone Docker Compose path in [`docs/deploy.md`](../deploy.md).

Goals:

- Know where **content** lives vs where **code** lives vs what **HTTPRoute** serves today.
- Ship UI/API changes via **git → image → Flux**, then **curl-verify**.
- Keep the **TestFlight privacy URL** healthy (or knowingly track the gate as open).
- Refuse unsafe moves: manual prod edits, force-pruning dirty worktrees, exposing held-out IP.

If you only need engine/API day-to-day (jobs, tracking, HealthKit tokens), start with [`docs/operators-manual.md`](../operators-manual.md). If you only need cluster failure modes, start with [`docs/server-management.md`](../server-management.md). **This doc is the website + restructure spine** that ties content paths, deploy topology, privacy gate, and agent skill discovery together.

---

## 2. Content sources (local paths)

| Priority | Absolute path | Role |
|----------|---------------|------|
| **PRIMARY corpus** | `/home/noahtjones/UF Dropbox/Noah Jones/Florida Man Bioscience/` | Pitch decks, roadmaps, PeptOdyssey dossier PDF, nanodisk reports, team photos, Figma export, workshop notes. Prefer human review before lifting clinical/investor claims into public HTML. |
| **Company knowledge base** | `/home/noahtjones/fmb-company` | Git remote `Florida-Man-Bioscience/company`. Brand, business-plan (incl. **Read → Predict → Report → Track → Deliver**), product modules, regulatory posture. |
| **Static marketing (not apex today)** | `/home/noahtjones/fmb-website` | Corporate `index.html`, static `/peptodyssey/privacy`, assets. README still markets this as flmanbiosci.net — **production HTTPRoute does not serve this image**. |
| **Live product UI source** | `/home/noahtjones/u4u-engine` (+ worktrees under `…/u4u-engine/.worktrees/`) | Next.js under `frontend/`; FastAPI under `api.py` / `engine/`. **This is what apex `/*` hits.** |
| **iOS app** | `/home/noahtjones/peptodyssey` | Hard-depends on privacy URL + `/api/v1`. Checklists under `docs/TESTFLIGHT_CHECKLIST.md`, `docs/PRIVACY.md` / `PRIVACY_LABEL.md`. |
| **GitOps / cluster** | `/home/noahtjones/iac` | Remote `hwcopeland/iac`. Manifests for `theswamp`, gateway, DNS. |

### Explicit non-sources

| Path | Why ignore for website copy |
|------|------------------------------|
| `/home/noahtjones/Florida Man Bioscience` | Obsidian vault with empty/near-empty dated notes — **not** the FMB content corpus. |
| `/home/noahtjones/Dropbox` (personal root) | No dedicated FMB website library (academic dump only). |
| Arete / Hermes memory alone | May summarize; **always** re-open the Dropbox / `fmb-company` paths above for claims. |

**Tagline (brand):** “Peptide medicine, matched to the genome.”  
**Public triad in plan language:** Detect → Design → Deliver (plan `p-01184334`; not yet a long-standing published slogan in `fmb-company` — map carefully from the 5-stage internal loop).

---

## 3. Repo layout — what is on prod HTTPRoute today

### 3.1 Two “website” repos, one production owner

| Repo | Local path | Prod role **today** |
|------|------------|---------------------|
| **u4u-engine** | `/home/noahtjones/u4u-engine` | **Serves apex and app hosts.** Next frontend Deployment + API Deployment in `theswamp`. |
| **fmb-website** | `/home/noahtjones/fmb-website` | Marketing static site **ready in git**, **not** referenced by `theswamp` HTTPRoutes. |
| **fmb-company** | `/home/noahtjones/fmb-company` | Docs only — never served over HTTP. |
| **iac** | `/home/noahtjones/iac` | Cluster source of truth for routes, digests, RBAC. |

### 3.2 Production routing (live contract)

Source: `/home/noahtjones/iac/rke2/tooling/flux/theswamp/httproute.yaml` (+ `httproute-www-redirect.yaml`).

| Host | Path | Backend |
|------|------|---------|
| `flmanbiosci.net` | `/api/v1/*` | Service `u4u-engine:8000` after **prefix strip** `/api/v1` → `/` |
| `flmanbiosci.net` | `/*` | Service `u4u-engine-frontend:3000` |
| `app.flmanbiosci.net` | same split | Same frontend + API rewrite (product mirror host) |
| `api.flmanbiosci.net` | `/*` | API at **root** (no `/api/v1` prefix) |
| `www.flmanbiosci.net` | `/*` | **301** → `https://flmanbiosci.net` |

Gateway: Cilium **`hwcopeland-gateway`** in `kube-system`. Apex HTTPS listener section name: `flmanbiosci-root-https`; wildcard / app / api listeners use `flmanbiosci-https`.

**Implication for restructure:** putting a company home at `/` and PeptOdyssey under `/peptodyssey/*` is a **Next frontend (or HTTPRoute) change**, not “flip DNS to fmb-website,” unless someone deliberately adds a second backend and path-split rules. Prefer implementing IA inside **u4u-engine `frontend/`** unless an explicit route redesign is approved and committed to `iac` `main`.

### 3.3 Kustomization inventory

Absolute tree:

```text
/home/noahtjones/iac/rke2/tooling/flux/theswamp/
  ACCESS.md
  namespace.yaml
  zot-pull-secret.yaml
  postgres.yaml
  deployment.yaml              # api image pin + $imagepolicy
  deployment-frontend.yaml     # frontend image pin + $imagepolicy
  service.yaml
  service-frontend.yaml
  httproute.yaml
  httproute-www-redirect.yaml
  rbac.yaml
  kustomization.yaml
```

`kustomization.yaml` currently lists the resources above (including `postgres.yaml`). **Flux only applies what is on `origin/main` of `hwcopeland/iac`.** Local dirty/unpushed edits do nothing.

---

## 4. Deploy path — Cloudflare → Cilium Gateway → Flux GitOps

```text
Internet
  → Cloudflare (proxied DNS for flmanbiosci.net)
  → Cilium Gateway  (hwcopeland-gateway, kube-system)
  → HTTPRoute (theswamp/u4u-engine[…])
       /api/v1/*  → u4u-engine (:8000)   [prefix rewritten to /]
       /*         → u4u-engine-frontend (:3000)
  → api talks to in-cluster Postgres (when DATABASE_URL / secrets are wired)
```

| Piece | Value |
|-------|--------|
| Namespace | `theswamp` |
| Manifest tree | `/home/noahtjones/iac/rke2/tooling/flux/theswamp/` |
| Image automation | `/home/noahtjones/iac/rke2/tooling/flux/image-automation/` |
| Registry | `zot.hwcopeland.net/florida-man-bioscience/` |
| Images | `u4u-engine`, `u4u-engine-frontend` (tags `main` + short SHA; Flux pins **digest**) |
| Secrets | External Secrets Operator ← Bitwarden / Vaultwarden |
| CI runners | GitHub Actions `runs-on: [self-hosted, hwcopeland]` (cluster ARC) |

### Normal release loop (no manual kubectl)

1. Merge/push to **`u4u-engine` `main`**.
2. Workflows build/push images to Zot (`build-and-push.yml`, `build-and-push-frontend.yml`). Frontend workflow is path-filtered on `frontend/**` and bakes `NEXT_PUBLIC_API_BASE` at build time.
3. Flux `ImageRepository` / `ImagePolicy` in namespace **`tooling`** notice the new digest.
4. `ImageUpdateAutomation` rewrites digests in `deployment.yaml` / `deployment-frontend.yaml` via the `# {"$imagepolicy": "tooling:…"}` comments and commits to **`iac` `main`** as `fluxcdbot`.
5. Flux reconciles kustomization **`theswamp`** → rolling update.

**Never delete or reformat the `$imagepolicy` comments** — automation silently stops without them.

### Hostnames / images quick table

| Public URL | Image / service |
|------------|-----------------|
| `https://flmanbiosci.net/` | `u4u-engine-frontend` |
| `https://flmanbiosci.net/api/v1/<path>` | `u4u-engine` (path rewritten) |
| `https://app.flmanbiosci.net/` | same frontend |
| `https://api.flmanbiosci.net/health` | `u4u-engine` root |

Standalone Compose path ([`docs/deploy.md`](../deploy.md)) is for throwaway/local-prod parity only — **not** apex.

---

## 5. hwcopeland server runbook — found on disk

### 5.1 Primary FMB / u4u production runbook (**found**)

| Doc | Absolute path |
|-----|---------------|
| **Server management & production deployment** | `/home/noahtjones/u4u-engine/docs/server-management.md` |
| Same file in this worktree | `/home/noahtjones/u4u-engine/.worktrees/t_af09bfbc/docs/server-management.md` |
| Repo-relative | `docs/server-management.md` |

**What it covers (summary — do not replace it):**

- Prod vs Compose dual path.
- Topology: Cloudflare → Cilium Gateway → HTTPRoute → Deployments → Postgres.
- Full GitOps release chain and image-policy markers.
- Failure-mode map: unpushed iac manifests, ExternalSecret / Bitwarden UUID, ImagePullBackOff, Flux image automation stuck, self-hosted runner down, HTTPRoute `sectionName` mismatch, OOM.
- **Safe kubectl scope:** namespace `theswamp` only for FMB collaborators.
- Quick commands: `kubectl -n theswamp get/logs/rollout`, `flux get image … -n tooling`, `flux reconcile kustomization theswamp --with-source`.

### 5.2 Companion iac docs (**found**)

| Doc | Absolute path | Use when |
|------|---------------|----------|
| Collaborator kubectl access | `/home/noahtjones/iac/rke2/tooling/flux/theswamp/ACCESS.md` | Mint `swamp-dev` token / OIDC kubelogin |
| Cluster overview (authoritative iac) | `/home/noahtjones/iac/CLAUDE.md` | Nodes, namespaces, networking, secrets, CI |
| Grafana “Swamp” folder ops | `/home/noahtjones/iac/rke2/chem/khemeia/docs/swamp-management-runbook.md` | FMB Editor/Admin on Grafana folder; Authentik group onboarding |
| Engine operator manual | `/home/noahtjones/u4u-engine/docs/operators-manual.md` | App config, not gateway |

### 5.3 SSH / kubectl / flux — safe habits

1. **Network:** kube-apiserver must be reachable (home LAN / VPN). RBAC ≠ reachability.
2. **Auth:** prefer time-boxed `kubectl -n theswamp create token swamp-dev --duration=…` or OIDC (`auth.hwcopeland.net`) per ACCESS.md — not long-lived tokens in chat logs.
3. **Read before write:**
   ```sh
   kubectl -n theswamp get pods,httproute,deploy
   kubectl -n theswamp describe httproute u4u-engine
   flux get kustomization -A
   flux get image all -n tooling
   ```
4. **Prefer GitOps over imperative apply.** Normal ship = fix code → green CI image → wait for Flux digest commit. Use `flux reconcile kustomization theswamp --with-source` only to **nudge** after `iac` `main` already has the desired state.
5. **Do not** `kubectl apply -f` random local YAML that is not on `origin/main` and expect permanence — Flux will overwrite on next reconcile.
6. **Do not** edit live Secrets/ConfigMaps as the long-term fix; fix Bitwarden / ExternalSecret / git.
7. **SSH to nodes** is platform-owner territory (ansible inventory in `iac/ansible/`). FMB app work should almost never need node SSH.

### 5.4 Search roots used for this section

Searched (2026-08-04, this task):

- `find /home/noahtjones -maxdepth 4` for `*hwcopeland*`, `*server-management*`, `*runbook*`
- `/home/noahtjones/iac` tree (including `rke2/chem/khemeia/docs/`)
- `/home/noahtjones/u4u-engine/docs/`

**Not found as a separate “home-dir only” hwcopeland personal runbook** outside the u4u-engine + iac paths above. Stale iac docs (`iac/docs/TROUBLESHOOTING.md`, older Canal/MetalLB/ArgoCD descriptions) are **explicitly distrusted** by `server-management.md` — trust `iac/CLAUDE.md` + live manifests instead.

---

## 6. Hermes skill — search result

### 6.1 Dedicated skill for “operate hwcopeland / theswamp / flmanbiosci deploy”

**Not found.** There is **no** Hermes skill whose primary job is FMB cluster/server ops (no `theswamp-ops`, `hwcopeland-server`, or `flmanbiosci-ops` skill under the roots below).

### 6.2 Roots searched

| Root | Result |
|------|--------|
| `/home/noahtjones/.hermes/skills/**/SKILL.md` | Present; no dedicated cluster skill |
| `/home/noahtjones/hermes/skills` | **Path does not exist** |
| `/data/.hermes/skills` | **Path does not exist** |
| `/home/noahtjones/.hermes/profiles/**` | No extra profile skill for theswamp |
| `u4u-engine` repo | No first-party `skills/` tree for ops |

Content search (`hwcopeland`, `theswamp`, `flmanbiosci`, `server-management`) hit only **tangential** skills.

### 6.3 Closest skills (load these instead — do not invent a missing one)

| Skill name | Absolute path | When agents must load it |
|------------|---------------|--------------------------|
| **`arete-portfolio`** | `/home/noahtjones/.hermes/skills/software-development/arete-portfolio/SKILL.md` | Portfolio / multi-opco work including **PeptOdyssey production gate** (privacy URL 200, Flux/frontend lag diagnosis notes). |
| **`arete-chief-of-staff`** | `/home/noahtjones/.hermes/skills/software-development/arete-chief-of-staff/SKILL.md` | Plan task routing, journal notes, handoffs for `p-01184334`. |
| **`hermes-ops`** | `/home/noahtjones/.hermes/skills/autonomous-ai-agents/hermes-ops/SKILL.md` | Hermes *agent* day-to-day (managed install, MCP RAM, Signal, OptMem) — **not** the Kubernetes cluster. |
| **`demo-websites`** | `/home/noahtjones/.hermes/skills/software-development/demo-websites/SKILL.md` | FMWS demo catalog on **floridamanweb.online** (also uses Zot); **not** flmanbiosci.net apex. |
| **`kanban-worktree-hygiene`** | under `/home/noahtjones/.hermes/skills/autonomous-ai-agents/kanban-worktree-hygiene/` | Before creating kanban worktrees on shared repos — exclusive trees, no force-prune dirty. |
| **`github-workflows`** | `/home/noahtjones/.hermes/skills/github/github-workflows/SKILL.md` | Debugging failed frontend image CI (root cause of privacy 404 lag). |

**Agent rule of thumb:** for flmanbiosci.net production behavior, **read this OPS runbook + `docs/server-management.md` + iac ACCESS.md** first. Load `arete-portfolio` when coordinating PeptOdyssey/TestFlight gates across repos. Do **not** load `demo-websites` expecting flmanbiosci deploy steps.

**Gap to close later (out of this task):** author a small Hermes skill (e.g. `flmanbiosci-ops` or `theswamp-ops`) that points at this file + server-management + ACCESS.md. Until then, **this markdown is the agent contract**.

---

## 7. Privacy / TestFlight gate

### 7.1 Canonical URL (frozen)

```text
https://flmanbiosci.net/peptodyssey/privacy
```

Must remain **HTTP 200** forever (path frozen for App Store / TestFlight). Also check the app host mirror:

```text
https://app.flmanbiosci.net/peptodyssey/privacy
```

### 7.2 Source of record

| Artifact | Path / ref |
|----------|------------|
| Next page (prod owner of record) | `frontend/src/app/peptodyssey/privacy/page.tsx` in u4u-engine |
| Absolute (this worktree) | `/home/noahtjones/u4u-engine/.worktrees/t_af09bfbc/frontend/src/app/peptodyssey/privacy/page.tsx` |
| Commit on main that added it | `05cf429` — *feat: host PeptOdyssey iOS privacy policy at /peptodyssey/privacy* |
| Static mirror (not on apex route) | `/home/noahtjones/fmb-website/peptodyssey/privacy/index.html` |
| iOS pin | `peptodyssey` app `AppLinks.privacyPolicy` / TestFlight docs |

### 7.3 Live failure mode (as of sibling verify 2026-08-03/04)

- **Live:** privacy still **404** while source is on `main`.
- **Cause class:** frontend container **image lag** — CI “build and push frontend” failing (TypeScript / peer dependency hell after compile), so Flux never advances digest; cluster keeps old frontend (e.g. **v1.0.137**) without the privacy route.
- **Not fixed by:** editing Swift alone, pointing DNS at fmb-website without HTTPRoute change, or documenting harder.

Track / sibling plan tasks: privacy deploy gate (`t-pept-privacy-url` / peptodyssey-ship), verify gate `docs/VERIFY.md` on worktree `t_0a90b71d`.

### 7.4 Rollout checklist when frontend image lags `main`

1. Confirm source on `origin/main`:
   ```sh
   git -C /home/noahtjones/u4u-engine ls-tree -r origin/main --name-only | grep 'peptodyssey/privacy'
   ```
2. Confirm live HTTP:
   ```sh
   curl -sS -o /dev/null -w "%{http_code}\n" https://flmanbiosci.net/peptodyssey/privacy
   curl -sS -o /dev/null -w "%{http_code}\n" https://app.flmanbiosci.net/peptodyssey/privacy
   ```
3. Inspect GitHub Actions **build and push frontend container** on `main` — last green vs red; fix TS/deps so image publishes to Zot.
4. Confirm Zot has a new digest; Flux policy advanced:
   ```sh
   flux get image repository u4u-engine-frontend -n tooling
   flux get image policy u4u-engine-frontend -n tooling
   ```
5. Confirm `iac` `deployment-frontend.yaml` digest moved on `origin/main` and pod rolled:
   ```sh
   kubectl -n theswamp rollout status deploy/u4u-engine-frontend
   kubectl -n theswamp get deploy u4u-engine-frontend -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
   ```
6. Re-curl privacy until **200**; only then close TestFlight privacy tasks.
7. **Emergency path (human owner decision only):** temporary HTTPRoute path for privacy → static backend, or hotfix image — never silently rewrite the public path.

---

## 8. Safe change procedure

### 8.1 Standard path (preferred)

```text
1. Exclusive git worktree / branch (kanban or manual) — never steal a dirty peer tree
2. Implement in the correct repo (usually u4u-engine frontend/ or api)
3. Local verify (nix develop / npm build / pytest as applicable)
4. PR → merge to main
5. Watch CI image build (frontend AND/OR api)
6. Wait for Flux digest commit on hwcopeland/iac OR reconcile after iac main is correct
7. curl-verify public URLs (below)
8. Journal / leave PR URL + commit SHAs for humans
```

### 8.2 Verify commands (copy/paste)

```sh
# Health
curl -sS https://flmanbiosci.net/api/v1/health
curl -sS https://api.flmanbiosci.net/health

# Site + privacy gate
curl -sS -o /dev/null -w "%{http_code} %{url_effective}\n" https://flmanbiosci.net/
curl -sS -o /dev/null -w "%{http_code}\n" https://flmanbiosci.net/peptodyssey/privacy
curl -sS -o /dev/null -w "%{http_code}\n" -L --max-redirs 0 https://www.flmanbiosci.net/

# Optional: show frontend version string from HTML footer when present
curl -sS https://flmanbiosci.net/ | tr '\n' ' ' | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head
```

### 8.3 Manifest-only changes (iac)

1. Edit under `/home/noahtjones/iac/rke2/tooling/flux/theswamp/` (or image-automation).
2. Ensure file is listed in `kustomization.yaml` if new.
3. **Commit + push to `iac` `main`** (or PR per house rules).
4. `flux reconcile kustomization theswamp --with-source` if impatient.
5. `kubectl -n theswamp describe httproute …` / `get pods` / curl.

### 8.4 What NOT to do

| Forbidden | Why |
|-----------|-----|
| Manual long-lived prod edits (`kubectl edit deploy`, patch images by hand) without git | Flux reverts; next human cannot audit |
| Force-prune / `git worktree remove --force` on **dirty** peer worktrees | Destroys exclusive agent state |
| Expose held-out IP (e.g. Harmonia NSF, erv-immune Oxford) on public pages | Legal / partnership stop-the-line — escalate to Noah |
| Invent clinical/FDA claims or tax/ownership facts | Not in scope; use `fmb-company/regulatory` + counsel |
| Assume fmb-website is live because README says so | HTTPRoute proves otherwise |
| Close TestFlight privacy tasks while curl is still 404 | Gate is objective |
| Delete `# {"$imagepolicy": …}` comments | Breaks auto-rollout |
| Cluster mutations from pure documentation cards | This task class is read/docs only |
| Commit secrets, tokens, kubeconfigs into u4u-engine | Use Bitwarden / ACCESS.md paths |

### 8.5 Worktree hygiene (agents)

- One exclusive worktree per agent/task (`…/u4u-engine/.worktrees/<task-id>`).
- Load **`kanban-worktree-hygiene`** before spawning more repo-touching kanban cards.
- Salvage timed-out agents onto a salvage branch — do not wipe dirty trees.

---

## 9. Pointers

| Artifact | Where |
|----------|--------|
| **This runbook** | `docs/website/OPS_RUNBOOK.md` · `/home/noahtjones/u4u-engine/.worktrees/t_af09bfbc/docs/website/OPS_RUNBOOK.md` |
| Website drafts index | `docs/website/README.md` (this tree) |
| **Site inventory** (sibling worktree until merged) | `/home/noahtjones/u4u-engine/.worktrees/t_f12a9f1a/docs/SITE_INVENTORY.md` · expected merge path `docs/SITE_INVENTORY.md` |
| **IA proposal** (sibling) | `/home/noahtjones/u4u-engine/.worktrees/t_ad15f7e7/docs/website/IA.md` and `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/docs/website/IA.md` · expected `docs/website/IA.md` |
| Content drafts | `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/docs/website/content/` |
| **VERIFY gate** (sibling) | `/home/noahtjones/u4u-engine/.worktrees/t_0a90b71d/docs/VERIFY.md` |
| Production cluster runbook | `docs/server-management.md` |
| Compose-only deploy | `docs/deploy.md` |
| Collaborator kubectl | `/home/noahtjones/iac/rke2/tooling/flux/theswamp/ACCESS.md` |
| Arete plan project | `p-01184334` — FMB website (flmanbiosci.net) restructure |
| PeptOdyssey privacy ship | plan/sibling `t-pept-privacy-url` / peptodyssey TestFlight checklist — keep open until privacy **200** |
| Hermes closest skill | `arete-portfolio` (gate notes) — **no dedicated theswamp skill** (see §6) |

### Cross-link maintenance

When merging sibling docs into `main`, add a short “Ops” pointer back here:

- In `docs/SITE_INVENTORY.md`: link **Operator runbook → [`docs/website/OPS_RUNBOOK.md`](website/OPS_RUNBOOK.md)**.
- In `docs/website/IA.md`: link **Deploy / ops → [`OPS_RUNBOOK.md`](./OPS_RUNBOOK.md)**.
- `docs/server-management.md` already points at cluster detail; keep a one-liner to this website OPS spine (see footer note in that file when present).

---

## Document control

| Field | Value |
|-------|--------|
| Created | 2026-08-04 |
| Authoring task | Arete `t-fmbweb-ops-docs` / kanban `t_af09bfbc` |
| Cluster mutations in task | **None** |
| hwcopeland runbook found? | **Yes** — `docs/server-management.md` + iac ACCESS + swamp Grafana runbook |
| Hermes theswamp skill found? | **No** — closest `arete-portfolio`; gap noted in §6 |
