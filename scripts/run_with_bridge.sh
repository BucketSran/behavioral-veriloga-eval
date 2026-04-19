#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: ./scripts/run_with_bridge.sh <command> [args...]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT_DIR/.." && pwd)"
DEFAULT_BRIDGE_REPO="$PROJECT_ROOT/../iccad/virtuoso-bridge-lite"
BRIDGE_REPO="${BRIDGE_REPO:-$DEFAULT_BRIDGE_REPO}"
BRIDGE_ENV="${BRIDGE_ENV:-$BRIDGE_REPO/.env}"

if [[ ! -f "$BRIDGE_ENV" ]]; then
  echo "bridge env not found: $BRIDGE_ENV" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$BRIDGE_ENV"
set +a

: "${VB_REMOTE_HOST:?VB_REMOTE_HOST missing in $BRIDGE_ENV}"
: "${VB_REMOTE_USER:?VB_REMOTE_USER missing in $BRIDGE_ENV}"
: "${VB_REMOTE_PORT:=65081}"
: "${VB_LOCAL_PORT:=65082}"

cleanup() {
  local pids
  pids="$(lsof -tiTCP:${VB_LOCAL_PORT} -sTCP:LISTEN -n -P || true)"
  if [[ -n "$pids" ]]; then
    kill $pids >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "starting temporary bridge tunnel on localhost:${VB_LOCAL_PORT}" >&2
SSH_ARGS=(
  -f
  -o BatchMode=yes
  -o StrictHostKeyChecking=no
  -o ExitOnForwardFailure=yes
)

if [[ -n "${VB_JUMP_HOST:-}" ]]; then
  SSH_ARGS+=(-J "${VB_JUMP_USER:-$VB_REMOTE_USER}@${VB_JUMP_HOST}")
fi

ssh "${SSH_ARGS[@]}" "${VB_REMOTE_USER}@${VB_REMOTE_HOST}" -L "${VB_LOCAL_PORT}:127.0.0.1:${VB_REMOTE_PORT}" -N

python3 "$ROOT_DIR/runners/bridge_preflight.py" --bridge-repo "$BRIDGE_REPO" >/dev/null
export VAEVAS_BRIDGE_WRAPPER=1
export VAEVAS_BRIDGE_REPO="$BRIDGE_REPO"
export VAEVAS_BRIDGE_ENV="$BRIDGE_ENV"
"$@"
