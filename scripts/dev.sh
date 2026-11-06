#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="${DEV_RUN_DIR:-/tmp/sami-dev}"
LAYA_CHECKPOINT="${LAYA_CHECKPOINT:-$ROOT/Training/sap-intent-v2}"
LAYA_MODEL_NAME="${LAYA_MODEL_NAME:-sap-intent-v2}"
mkdir -p "$RUN"
cd "$ROOT"

listening() { ss -ltn | grep -q ":$1 "; }

start() {
  local name=$1 port=$2
  shift 2
  if listening "$port"; then
    echo "$name: port $port already in use, left alone"
    return
  fi
  setsid nohup "$@" >"$RUN/$name.log" 2>&1 &
  echo $! >"$RUN/$name.pid"
  echo "$name: starting on $port (log $RUN/$name.log)"
}

stop() {
  for f in "$RUN"/*.pid; do
    [ -e "$f" ] || continue
    kill -- "-$(cat "$f")" 2>/dev/null
    rm -f "$f"
    echo "stopped $(basename "$f" .pid)"
  done
}

status() {
  for p in 8001:auth-api 8002:workspace-api 8003:butterfly 8004:synapse-api 8006:intent-api 8011:laya 5173:workspace-web 5174:synapse-web 5176:admin-web; do
    if listening "${p%%:*}"; then echo "up    ${p#*:} (${p%%:*})"; else echo "down  ${p#*:} (${p%%:*})"; fi
  done
}

case "${1:-start}" in
  start)
    if command -v docker >/dev/null && [ -d "$LAYA_CHECKPOINT" ]; then
      docker compose up -d --wait intent-classifier
    else
      echo "laya: Docker or $LAYA_CHECKPOINT missing, skipped (intent-api will answer cannot_classify_now)"
    fi
    start butterfly 8003 uv run --package butterfly butterfly
    start auth-api 8001 uv run --package auth-api python -m auth_api.entrypoint.app
    JWT_SECRET="$(grep -m1 '^JWT_SECRET=' "$ROOT/.env" | cut -d= -f2-)" FRONTEND_URL=http://localhost:5173 \
      start workspace-api 8002 uv run --package workspace-api workspace-api
    start synapse-api 8004 uv run --package synapse-api synapse-api
    LAYA_URL=http://localhost:8011 LAYA_MODEL="$LAYA_MODEL_NAME" DOMAIN_MIN_PROBABILITY=0.4 \
      start intent-api 8006 uv run --package intent-api intent-api
    start workspace-web 5173 pnpm --filter workspace-web exec vite --port 5173 --strictPort
    start synapse-web 5174 pnpm --filter synapse-web exec vite --port 5174 --strictPort
    start admin-web 5176 pnpm --filter admin-web exec vite --port 5176 --strictPort
    ;;
  stop) stop; docker compose stop intent-classifier 2>/dev/null ;;
  status) status ;;
  *) echo "usage: scripts/dev.sh [start|stop|status]"; exit 2 ;;
esac
