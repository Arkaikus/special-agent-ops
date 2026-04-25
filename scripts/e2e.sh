#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== docker compose: redis + gateway"
docker compose up -d redis gateway

echo "== wait for gateway"
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:8000/health" >/dev/null; then
    echo "gateway ok"
    exit 0
  fi
  sleep 1
done

echo "gateway failed to become healthy" >&2
exit 1
