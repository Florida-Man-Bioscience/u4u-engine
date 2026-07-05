# Security hardening — findings, fixes, and the access-control roadmap

_Status: 2026-07-05. This documents a security audit of the u4u-engine backend +
frontend, what the accompanying PR fixes, and the **coordinated** work still
required (infra + backend + frontend) to close the critical access-control gaps._

> **The #1 risk is infrastructure that this repo cannot fix on its own.** In
> production the API sits behind the Cilium gateway with **no forward-auth**, and
> the backend derives identity from client-supplied `X-Authentik-*` headers that
> nothing strips. Until the gateway enforces auth and strips those headers, the
> API is effectively unauthenticated regardless of any code change here.

## Audit summary (severity-ranked)

Cryptography, randomness, token handling, and SQL are **clean** (CSPRNG ids/tokens,
SHA-256 of 256-bit tokens, parameterized queries throughout, HTTPS to all external
APIs, non-root containers). The risk is concentrated in **access control**.

| # | Finding | Severity | Layer |
|---|---------|----------|-------|
| A1 | No forward-auth in front of the backend; `current_user` trusts spoofable `X-Authentik-*` headers (`engine/users/deps.py`, `engine/users/service.py`). Verified in iac: the `theswamp` HTTPRoutes carry only `URLRewrite` filters, no `forwardAuth`, and don't strip inbound identity headers. | **CRITICAL** | infra + code |
| A2 | IDOR — every `/jobs/*` and `/tracking/*` **read** is scoped only by an unguessable id; `created_by_user_id` is written but never in a `WHERE`. `GET /jobs` and `GET /tracking/patients` enumerate ids, defeating unguessability. | **CRITICAL** | code |
| A3 | Unauthenticated destructive endpoints: `POST /tracking/seed {force:true}` (FK-cascade wipe) and `DELETE /tracking/patients/{id}`. | **CRITICAL** | code |
| A4 | `POST /jobs/{job}/variants/{v}/acmg-signoff` — unauthenticated clinical sign-out with a **client-supplied `reviewer`** string; forgeable medical determination. | **HIGH** | code |
| A5 | `GET /users` returns all users + emails, unauthenticated (PII harvest). | **HIGH** | code |
| A6 | `/analyze` decompression bomb + unbounded parse memory; body fully buffered before the size check; no ingress body cap; no rate limiting. | **HIGH/MED** | code + infra |
| A7 | HealthKit `POST /samples` uses `enforce_subject(...)` **without** `require_bound`, so an unbound token can write any `subject_id` (cross-subject data poisoning). Deliberate in PR #50, but worth revisiting. | **MED** | code |
| A8 | No dependency/CVE scanning in CI; floating `>=` pins; `chmod 777 /app/data`; stale unused `bcrypt`; no in-app security headers; `ALLOWED_ORIGINS=*`+credentials footgun. | **LOW/MED** | infra + code |

## Fixed in the accompanying PR (identity-independent, non-breaking)

These need no trustworthy identity, so they ship now without touching the live
app's (currently open) behaviour:

- **Decompression-bomb cap** — `engine/parsers.py` aborts once a file yields more
  than `MAX_VARIANTS` (default 6M, env-overridable), bounding memory and stopping
  lazy decompression (A6, partial).
- **Bounded upload read** — `api.py` reads at most `MAX_UPLOAD_MB+1` so an oversized
  body is rejected without materialising multi-GB in RAM (A6, partial; the ingress
  body cap remains an infra task).
- **`/tracking/seed` force-wipe guard** — refuses `force=true` when the tracking
  store is Postgres (`_is_pg`), i.e. production (A3, partial — the wipe primitive).
- **Baseline security headers** — `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, HSTS on every response (A8).
- **CORS wildcard guard** — `ALLOWED_ORIGINS=*` disables `allow_credentials` rather
  than honour the unsafe combo (A8).
- **Stop logging PHI filenames** — `/analyze` logs the extension only (A8).
- **CI dependency scanning** — `pip-audit` + `npm audit` workflow + Dependabot (A8).
- **Hygiene** — `chmod 700` on the data dir, removed unused `bcrypt`, least-privilege
  `permissions:` on the test workflow (A8).

## The access-control core — coordinated, NOT shipped here

A2–A5 are the critical gaps, but every fix needs a **trustworthy identity**, which
does not exist until the proxy lands. Shipping backend auth against spoofable
headers would be theatre; shipping it behind a default-off flag would rot. So this
is sequenced work, not a solo backend PR:

**Step 1 — Infra (owner: Hampton / `iac`), the linchpin.**
- Put an Authentik **forward-auth** filter in front of the `theswamp` backend
  HTTPRoutes (`flmanbiosci.net/api/v1/*`, `app.…`, `api.…`) — the pattern already
  exists for Hubble (`rke2/kube-system/cilium/httproute-hubble.yaml`).
- **Strip inbound `X-Authentik-*`** at the gateway so only the proxy can set them.
- Add an **ingress request-body limit** and **rate limiting** at the gateway.

**Step 2 — Backend (only meaningful after Step 1).**
- Enforce ownership: add `WHERE created_by_user_id = <caller>` to every `/jobs/*`
  and `/tracking/*` read/delete; scope `GET /jobs` and `GET /tracking/patients` to
  the caller; require auth (`Depends(required_user)`) on all of them.
- `acmg-signoff`: require an authenticated reviewer and record the **verified**
  identity, not the request body (21 CFR Part 11 non-repudiation, per
  `engine/acmg/signoff.py`).
- `GET /users`: require an admin role.
- Recommend rolling this out **on by default** (not behind a flag) once Step 1 is
  live, with tests exercising the ownership filter.

**Step 3 — Frontend.**
- Ensure the app authenticates through the proxy (forward-auth cookie / redirect)
  so authenticated calls carry identity end-to-end.

**Also decide (not changed here):** HealthKit write scoping (A7) — either require a
subject-bound token on `POST /healthkit/samples` too, or make it env-configurable
with the current unbound-write default. This reverses a deliberate PR #50 choice,
so it's a product decision, not a silent flip.

## Infra / deployment recommendations (owner: Hampton)

- Confirm the prod `ALLOWED_ORIGINS` is an explicit allowlist, never `*` with credentials.
- Ingress body-size limit + rate limiting at the Cilium gateway (defense for A6).
- At-rest encryption for the Postgres volume (PHI) — infra, not a code guarantee.
- Ensure `sslmode` is not `disable` for any non-local DSN; don't publish `5432`.
- Keep `HEALTHKIT_REQUIRE_TOKEN`/`DATABASE_URL` set in prod (fail-closed auth).
