#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT_DIR/.." && pwd)"
DEFAULT_BRIDGE_REPO="$PROJECT_ROOT/../iccad/virtuoso-bridge-lite"
BRIDGE_REPO="${BRIDGE_REPO:-$DEFAULT_BRIDGE_REPO}"

python3 "$ROOT_DIR/runners/bridge_preflight.py" --bridge-repo "$BRIDGE_REPO" "$@"
