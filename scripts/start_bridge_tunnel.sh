#!/usr/bin/env bash
set -euo pipefail

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

: "${VB_REMOTE_PORT:=65081}"
: "${VB_LOCAL_PORT:=65082}"

if lsof -tiTCP:"$VB_LOCAL_PORT" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo "bridge tunnel already listening on localhost:$VB_LOCAL_PORT"
else
  : "${VB_REMOTE_HOST:?VB_REMOTE_HOST missing in $BRIDGE_ENV}"
  : "${VB_REMOTE_USER:?VB_REMOTE_USER missing in $BRIDGE_ENV}"
  SSH_ARGS=(
    -f
    -o BatchMode=yes
    -o StrictHostKeyChecking=no
    -o ExitOnForwardFailure=yes
  )
  if [[ -n "${VB_JUMP_HOST:-}" ]]; then
    JUMP_USER="${VB_JUMP_USER:-$VB_REMOTE_USER}"
    SSH_ARGS+=(-J "${JUMP_USER}@${VB_JUMP_HOST}")
  fi
  SSH_ARGS+=("${VB_REMOTE_USER}@${VB_REMOTE_HOST}" "-L" "${VB_LOCAL_PORT}:127.0.0.1:${VB_REMOTE_PORT}" "-N")
  ssh "${SSH_ARGS[@]}"
  echo "started bridge tunnel on localhost:$VB_LOCAL_PORT -> ${VB_REMOTE_HOST}:${VB_REMOTE_PORT}"
fi

python3 "$ROOT_DIR/runners/bridge_preflight.py" --bridge-repo "$BRIDGE_REPO"
