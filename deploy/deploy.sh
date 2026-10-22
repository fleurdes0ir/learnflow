#!/usr/bin/env bash
# PHASE 2 — dijalankan DI VM GCP oleh cd.yml (atau manual lewat SSH).
# Mode produksi = selalu `-f docker-compose.yml` (TANPA override hot-reload).
set -euo pipefail

cd "$(dirname "$0")/.."

[ -f .env ] || { echo "ERROR: .env tidak ada di $(pwd)" >&2; exit 1; }

docker compose -f docker-compose.yml up -d --build --remove-orphans --wait --wait-timeout 180

# Verifikasi dari sisi host (backend di-bind ke 127.0.0.1:8000).
curl --fail --silent --show-error --retry 5 --retry-delay 3 http://127.0.0.1:8000/healthz
echo

docker image prune -f >/dev/null
echo "Deploy OK: $(git rev-parse --short HEAD)"
