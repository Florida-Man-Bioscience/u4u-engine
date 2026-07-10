# Memo — peptodyssey app: what's needed to go live

**To:** Curtis
**From:** Noah
**Re:** Making HealthKit sync functional against the production engine
**Date:** 2026-07-04

The backend is **live and enforcing auth** in production. I've verified
`https://flmanbiosci.net/api/v1/healthkit/samples` returns `401` without a token
on both `GET` and `POST`. Everything below is the app-side work to talk to it.

Design/schema reference: [`healthkit-storage.md`](healthkit-storage.md) ·
setup/curl: [`healthkit-ingestion-setup.md`](healthkit-ingestion-setup.md).

---

## TL;DR — your checklist

1. [ ] Generate a stable **`subjectId`** (UUID v4) on first launch, store in Keychain, send it every upload.
2. [ ] Send me that `subjectId` so I can **mint a device token bound to it** (you can't mint it — needs cluster access). I'll hand you back the raw `pep_hk_…` token once.
3. [ ] Store the token in the **Keychain**; send it as `Authorization: Bearer <token>` on every request.
4. [ ] Point the app at base URL **`https://flmanbiosci.net/api/v1`**.
5. [ ] Build the JSON payload to **exactly** match the contract below (camelCase keys, `class`, ISO-8601 UTC).
6. [ ] Use `HKAnchoredObjectQuery` anchors so you only send deltas; re-sends are safe (idempotent).
7. [ ] Handle `401` / `403` / `422` explicitly (see below).

---

## 1. Authentication — interim device token (do this first)

The endpoint uses a **per-device bearer token** right now. It is required in prod;
there's no anonymous path.

- **You cannot mint it** — it's created with `scripts/create_healthkit_token.py`
  inside the cluster. **I mint it, you receive it.** The raw token is shown only
  once, so store it immediately.
- I'll mint it **bound to your `subjectId`** (`--subject <id>`). That matters:
  - a **bound** token may only read/write **that one subject** — good isolation;
  - **reads (`GET`) *require* a bound token** — an unbound token gets `403` on `GET`.
  So generate the `subjectId` first (step 2 below), send it to me, and I'll bind
  the token to it.
- Send it on **every** request:
  ```
  Authorization: Bearer pep_hk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

> **Longer term** this moves to Authentik (OAuth 2.0 device-code flow) for real
> per-user identity — not needed for launch. Details in `healthkit-storage.md`.

## 2. The `subjectId` (your pseudonymous key)

Generate **once, on first launch**: a random **UUID v4**. Persist it in the
**Keychain** and send it as `subjectId` on every upload.

- It's the de-identified key all rows are stored under — **no name/email/serial**.
- Keep it **stable** for the life of the install; regenerating it orphans prior data.
- This is what I bind your token to, so pick it before asking me for a token.

## 3. Base URL

| Environment | Base URL |
|---|---|
| **Production** | `https://flmanbiosci.net/api/v1` |
| Local (against your Mac) | `http://<mac-ip>:8000` |

The upload path is `/healthkit/samples` (unprefixed on the server — the `/api/v1`
prefix is stripped by the gateway). So the full prod URL is
`https://flmanbiosci.net/api/v1/healthkit/samples`.

## 4. Request contract — `POST /healthkit/samples`

Keys are **camelCase**; the sample kind field is literally named **`class`**;
all datetimes are **ISO-8601 UTC** (`2026-07-03T12:00:00Z`); `uuid` is the
device `HKSample.uuid` (this is what makes re-syncs idempotent).

```jsonc
{
  "subjectId": "5f2c…-uuid-v4",           // required, your Keychain id
  "samples": [
    {
      "uuid": "11111111-1111-…",           // HKSample.uuid — the idempotency key
      "class": "quantity",                 // "quantity" | "category" | "workout"
      "type": "HKQuantityTypeIdentifierHeartRate",
      "value": 62,                          // null for workouts/categories w/o a scalar
      "unit": "count/min",                  // null if not applicable
      "start": "2026-07-03T12:00:00Z",
      "end":   "2026-07-03T12:00:00Z",
      "source": { "name": "Apple Watch", "bundleId": "com.apple.health" },
      "device": { "name": "Watch", "model": "Watch7,1" },   // free-form object, optional
      "metadata": { },                     // free-form object, optional
      "workout": {                         // only when class == "workout", else omit/null
        "activityType": "running",
        "durationSeconds": 1800,
        "totalEnergyKcal": 250,
        "totalDistanceMeters": 5000
      }
    }
  ],
  "anchors": {                             // optional but recommended
    "HKQuantityTypeIdentifierHeartRate": "<base64 HKQueryAnchor>"
  }
}
```

**Response:** `{ "received": N, "inserted": M }` — `M` is genuinely-new rows.
Re-send the same `uuid` and it counts as `received` but `inserted: 0`.

Field notes:
- `subjectId` also accepts snake_case `subject_id`, but **use `subjectId`**.
- Unknown extra keys are ignored (the server is lenient), but the fields above
  are what get stored — anything else is dropped.
- `metadata` / `device` are stored as-is (JSON); put whatever HK gives you there.

## 5. Sync strategy (anchors + idempotency)

- Run an **`HKAnchoredObjectQuery` per type**, persist the returned anchor, and
  send it back in `anchors` so the next sync only ships deltas.
- Because ingestion is **insert-only keyed by `HKSample.uuid`**, resending is
  always safe — retry freely on network failure; duplicates become `inserted: 0`.
- **Known limitation to be aware of:** there is **no update / delete path** yet.
  If a sample is edited or deleted in HealthKit *after* it was synced, that change
  does **not** propagate — the first-seen version is retained. Fine for the
  "simple first" cut; flag it if the study needs mutable/deleted samples and I'll
  add a soft-delete path.

## 6. Reading data back — `GET /healthkit/samples`

```
GET /healthkit/samples?subject_id=<id>&type=<optional>&since=<ISO optional>&limit=<1..10000>
Authorization: Bearer <token BOUND to that subject_id>
```
Reads require a **subject-bound** token (unbound → `403`). Same token I mint you
works, since it's bound to your `subjectId`.

## 7. Error handling — what the status codes mean

| Code | Meaning | What to do |
|---|---|---|
| `200` | Accepted | Read `inserted` for how many were new. |
| `401` | Missing/invalid/revoked token | Token wrong or absent — re-check the `Authorization` header / ask me for a fresh token. |
| `403` | Token bound to a different subject, or unbound token on `GET` | You're using a token for the wrong `subjectId`, or trying to read with an unbound token. |
| `422` | Body doesn't match the schema | A field name/shape is off — compare against §4 (common culprits: missing `class`, non-UTC datetime, wrong key case). |

## 8. Quick smoke test (before wiring the app)

Once I've given you a token bound to a test `subjectId`:

```bash
curl -X POST https://flmanbiosci.net/api/v1/healthkit/samples \
  -H 'Authorization: Bearer <your token>' \
  -H 'Content-Type: application/json' \
  -d '{"subjectId":"<your test id>","samples":[{
        "uuid":"11111111-1111-1111-1111-111111111111",
        "class":"quantity","type":"HKQuantityTypeIdentifierHeartRate",
        "value":72,"unit":"count/min",
        "start":"2026-07-03T12:00:00Z","end":"2026-07-03T12:00:00Z",
        "source":{"name":"Apple Watch"}}]}'
# → {"received":1,"inserted":1}   (run again → inserted:0)
```

---

## What's on me (Noah), not you

- Minting your device token (bound to your `subjectId`) and handing it over securely.
- The eventual Authentik device-code migration (issuer + client_id provisioning is
  Hampton's Authentik task; you'll swap the interim token for the OAuth flow later).

Ping me with your `subjectId` and I'll get you a token.
