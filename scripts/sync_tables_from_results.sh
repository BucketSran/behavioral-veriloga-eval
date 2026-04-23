#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${ROOT}/results"
TABLES_DIR="${ROOT}/tables"

mkdir -p "${TABLES_DIR}"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -f "${src}" ]]; then
    cp "${src}" "${dst}"
    echo "[sync] copied: ${src} -> ${dst}"
  else
    echo "[sync] missing (skip): ${src}"
  fi
}

copy_if_exists \
  "${RESULTS_DIR}/table1-report-2026-04-21.md" \
  "${TABLES_DIR}/TABLE1_EVAS_VS_SPECTRE_GOLD.md"

copy_if_exists \
  "${RESULTS_DIR}/TABLE2_SUMMARY.md" \
  "${TABLES_DIR}/TABLE2_SUMMARY.md"

copy_if_exists \
  "${RESULTS_DIR}/TABLE2_FAILURE_ANALYSIS.md" \
  "${TABLES_DIR}/TABLE2_FAILURE_ANALYSIS.md"

echo "[sync] done"
