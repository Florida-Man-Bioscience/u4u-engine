#!/bin/sh
# scripts/docker-entrypoint.sh
# ============================
# Container startup hook for the u4u-engine API image.
#
# Runs the biomarker tracking demo seeder before launching the application
# when SEED_DEMO_DATA is enabled. The seeder is idempotent — if patients
# already exist (e.g. on a container restart or rolling deploy with a
# persistent volume) it exits without touching the DB.
#
# Failures in the seeder do not block the API from starting. Logs are
# emitted with a [entrypoint] prefix so they are easy to grep in container
# log aggregators.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SEEDER="${SCRIPT_DIR}/seed_tracking_data.py"

case "${SEED_DEMO_DATA:-0}" in
    1|true|True|TRUE|yes|on)
        echo "[entrypoint] SEED_DEMO_DATA=${SEED_DEMO_DATA} — running tracking seeder"
        if python "${SEEDER}"; then
            echo "[entrypoint] seeder completed"
        else
            rc=$?
            echo "[entrypoint] seeder exited with status ${rc} — continuing startup"
        fi
        ;;
    *)
        echo "[entrypoint] SEED_DEMO_DATA not set — skipping demo seeder"
        ;;
esac

exec "$@"
