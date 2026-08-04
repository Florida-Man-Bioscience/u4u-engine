# Postgres in-cluster hardening runbook — TLS in transit + at-rest encryption

_Status: 2026-07-11. Follow-through on the two infra items flagged in
[`security-hardening.md`](security-hardening.md): the `theswamp` Postgres DSN uses
`sslmode=disable`, and its Longhorn PVC is not encrypted at rest. Both hold PHI._

All manifests below live in the **`iac` repo** (`rke2/tooling/flux/theswamp/`),
owned by Hampton — they are **not** applied by this repo. Flux auto-reconciles
`theswamp`, so land each change as a reviewed PR, not a direct push to `main`.

Current wiring (verified 2026-07-11):
- `postgres.yaml` — `u4u-postgres` StatefulSet (`postgres:16-alpine`), headless
  Service `u4u-postgres.theswamp.svc.cluster.local:5432`, 10Gi `longhorn` PVC.
- `u4u-postgres-secret` ExternalSecret (Bitwarden) templates `POSTGRES_PASSWORD`
  and the full `DATABASE_URL` (currently `…?sslmode=disable`).
- `deployment.yaml` injects `DATABASE_URL` from that secret.
- Cluster has cert-manager (only `cf-issuer`, a Cloudflare DNS-01 issuer — cannot
  validate `.svc.cluster.local`). No `selfSigned`/CA issuer, no encrypted
  StorageClass, no Longhorn crypto secret exist yet.

---

## Matter 1 — TLS in transit (`sslmode=require`)  ·  LOW risk, do first

Goal: encrypt the app↔Postgres connection. `sslmode=require` encrypts without
CA verification, so a **self-signed server cert is sufficient** — no CA
distribution to the client needed. (Upgrade to `verify-full` later if desired;
that needs the CA bundle in the client DSN.)

**Server and client must land in the same PR** — flipping the DSN to `require`
before the server serves TLS breaks every connection.

### 1a. Add an internal self-signed issuer (new file `selfsigned-issuer.yaml`, or inline)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
```

### 1b. Server certificate for the Postgres service DNS names

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: u4u-postgres-tls
  namespace: theswamp
spec:
  secretName: u4u-postgres-tls          # produces tls.crt / tls.key
  duration: 8760h                        # 1y
  renewBefore: 720h                      # 30d
  privateKey:
    algorithm: ECDSA
    size: 256
  dnsNames:
    - u4u-postgres
    - u4u-postgres.theswamp
    - u4u-postgres.theswamp.svc
    - u4u-postgres.theswamp.svc.cluster.local
  issuerRef:
    kind: ClusterIssuer
    name: selfsigned-issuer
```

### 1c. Serve TLS from the StatefulSet

`postgres:16-alpine` runs as uid 70 and **refuses a key file that is group/world
readable or not owned by postgres**. A cert-manager secret mounts root-owned
0644, so copy it into an `emptyDir` with an initContainer. Patch the StatefulSet
pod spec:

```yaml
      # ── add to spec.template.spec ──
      initContainers:
        - name: fix-tls-perms
          image: postgres:16-alpine
          command: ["sh", "-c"]
          args:
            - |
              cp /tls-src/tls.crt /tls/server.crt
              cp /tls-src/tls.key /tls/server.key
              chown 70:70 /tls/server.crt /tls/server.key
              chmod 0600 /tls/server.key
              chmod 0644 /tls/server.crt
          volumeMounts:
            - { name: tls-src, mountPath: /tls-src, readOnly: true }
            - { name: tls, mountPath: /tls }
      # ── add to the postgres container ──
        # args (append to the container):
        #   args: ["-c","ssl=on","-c","ssl_cert_file=/tls/server.crt","-c","ssl_key_file=/tls/server.key"]
        # volumeMounts (append):
        #   - { name: tls, mountPath: /tls }
      # ── add to spec.template.spec.volumes ──
      volumes:
        - name: tls-src
          secret:
            secretName: u4u-postgres-tls
        - name: tls
          emptyDir: {}
```

(Add `args:` and the `tls` volumeMount to the existing `postgres` container; the
snippet shows them as comments to avoid ambiguity when editing the live file.)

### 1d. Flip the client DSN — same PR

In `postgres.yaml`, the ExternalSecret template:

```yaml
        DATABASE_URL: "postgresql://u4u:{{ .password }}@u4u-postgres.theswamp.svc.cluster.local:5432/u4u?sslmode=require"
```

### 1e. Rollout / verification
1. Merge PR → Flux applies. StatefulSet pod restarts (brief DB blip; app pod
   retries via the pool).
2. `kubectl -n theswamp exec u4u-postgres-0 -- psql -U u4u -c "show ssl;"` → `on`.
3. App `/health` green; a tracking read succeeds (proves `sslmode=require` works).
4. Rollback: revert the PR (DSN back to `disable`, drop TLS args).

**No app code change** — `db/pool.py` passes the DSN through verbatim; `require`
is honored by libpq/psycopg2.

---

## Matter 2 — At-rest encryption on the Longhorn PVC  ·  DESTRUCTIVE, schedule with Hampton

`storageClassName` is **immutable** on a StatefulSet `volumeClaimTemplate`, so
this is not an in-place edit — it requires recreating the volume behind a backup.
Needs a maintenance window and a Hampton decision on key management.

### 2a. Encryption key secret (Bitwarden-sourced, never hard-coded)

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: longhorn-crypto
  namespace: longhorn-system
spec:
  refreshInterval: "1h"
  secretStoreRef: { kind: ClusterSecretStore, name: bitwarden-login }
  target:
    name: longhorn-crypto
    creationPolicy: Owner
    template:
      engineVersion: v2
      data:
        CRYPTO_KEY_VALUE: "{{ .key }}"
        CRYPTO_KEY_PROVIDER: "secret"
        CRYPTO_KEY_CIPHER: "aes-xts-plain64"
        CRYPTO_KEY_HASH: "sha256"
        CRYPTO_KEY_SIZE: "256"
        CRYPTO_PBKDF: "argon2i"
  data:
    - secretKey: key
      remoteRef: { key: <BITWARDEN_UUID_FOR_LONGHORN_KEY>, property: password }
```

> ⚠️ Losing `CRYPTO_KEY_VALUE` = permanent loss of the volume. Back the Bitwarden
> item up before enabling.

### 2b. Encrypted StorageClass (new)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-encrypted
provisioner: driver.longhorn.io
allowVolumeExpansion: true
reclaimPolicy: Retain
parameters:
  numberOfReplicas: "2"
  staleReplicaTimeout: "30"
  encrypted: "true"
  csi.storage.k8s.io/provisioner-secret-name: longhorn-crypto
  csi.storage.k8s.io/provisioner-secret-namespace: longhorn-system
  csi.storage.k8s.io/node-publish-secret-name: longhorn-crypto
  csi.storage.k8s.io/node-publish-secret-namespace: longhorn-system
  csi.storage.k8s.io/node-stage-secret-name: longhorn-crypto
  csi.storage.k8s.io/node-stage-secret-namespace: longhorn-system
```

### 2c. Migration runbook (maintenance window)
1. **Backup**: `kubectl -n theswamp exec u4u-postgres-0 -- pg_dump -U u4u -Fc u4u > u4u-$(date).dump` and copy off-cluster.
2. Scale app to 0: `kubectl -n theswamp scale deploy/u4u-engine --replicas=0`.
3. In `postgres.yaml`, set the `volumeClaimTemplate.spec.storageClassName` to
   `longhorn-encrypted`. Because the field is immutable, delete the StatefulSet
   **and** its PVC first: `kubectl -n theswamp delete statefulset u4u-postgres`
   then `kubectl -n theswamp delete pvc postgres-data-u4u-postgres-0`.
4. Merge the PR → Flux recreates the StatefulSet on the encrypted SC (fresh empty
   volume).
5. **Restore**: `kubectl -n theswamp exec -i u4u-postgres-0 -- pg_restore -U u4u -d u4u --clean < u4u-*.dump`.
   `db/migrate.py` is idempotent (`schema_migrations`), so a subsequent app start
   re-checks migrations harmlessly.
6. Scale app back up; verify `/health` + a data read.
7. Confirm encryption: the Longhorn UI shows the volume `Encrypted: Yes`, or
   `kubectl -n longhorn-system get volumes.longhorn.io -o jsonpath …`.

Alternative (less downtime, more moving parts): Longhorn Backup → restore into a
new encrypted volume, then repoint. Hampton's call.

---

## Recommended sequencing
1. **Now**: Matter 1 (TLS) — self-contained, revert-able, no data risk.
2. **Scheduled window**: Matter 2 (at-rest) — needs backup + Hampton + a key in
   Bitwarden. Pairs naturally with the forward-auth proxy work (also Hampton, also
   `theswamp`), so both cluster-side security items land in one maintenance pass.
3. After both: update `security-hardening.md` (strike the two infra recs) and the
   `sslmode` note in this repo's `docs/deploy.md`.

Open decision for Hampton: `sslmode=require` (encrypt only, self-signed OK) vs.
`verify-full` (also authenticate the server — needs the CA cert in the client
DSN, i.e. templating `sslrootcert` and the CA into `u4u-postgres-secret`).
