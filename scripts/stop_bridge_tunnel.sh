#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT_DIR/.." && pwd)"
BRIDGE_REPO="$PROJECT_ROOT/../iccad/virtuoso-bridge-lite"
BRIDGE_ENV="$BRIDGE_REPO/.env"

if [[ ! -f "$BRIDGE_ENV" ]]; then
  echo "bridge env not found: $BRIDGE_ENV" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$BRIDGE_ENV"
set +a

: "${VB_LOCAL_PORT:=65082}"

PIDS="$(lsof -tiTCP:${VB_LOCAL_PORT} -sTCP:LISTEN -n -P || true)"
if [[ -z "$PIDS" ]]; then
  echo "no bridge tunnel listener found on localhost:$VB_LOCAL_PORT"
  exit 0
fi

kill $PIDS
echo "stopped bridge tunnel listener(s) on localhost:$VB_LOCAL_PORT: $PIDS"
