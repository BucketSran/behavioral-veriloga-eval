#!/usr/bin/env bash
set -euo pipefail

# Full MiMo-D run for benchmark-balanced under the unified spectre-strict-v3 protocol.
# Required environment:
#   MIMO_API_KEY=<redacted>
# Optional environment:
#   MIMO_BASE_URL=https://api.xiaomimimo.com/v1
#   MODEL=mimo-v2.5-pro
#   DATE_TAG=2026-05-04
#   GEN_WORKERS=2
#   SCORE_WORKERS=4
#   MAX_TOKENS=4096
#   TIMEOUT_S=240

if [[ -z "${MIMO_API_KEY:-}" ]]; then
  echo "[mimo-full] ERROR: MIMO_API_KEY is not set." >&2
  exit 1
fi

export MIMO_BASE_URL="${MIMO_BASE_URL:-https://api.xiaomimimo.com/v1}"
MODEL="${MODEL:-mimo-v2.5-pro}"
DATE_TAG="${DATE_TAG:-2026-05-04}"
GEN_WORKERS="${GEN_WORKERS:-2}"
SCORE_WORKERS="${SCORE_WORKERS:-4}"
MAX_TOKENS="${MAX_TOKENS:-4096}"
TIMEOUT_S="${TIMEOUT_S:-240}"

GEN_DIR="generated-balanced-D-strictv3-${MODEL}-${DATE_TAG}"
RESULT_DIR="results/balanced-D-strictv3-${MODEL}-spectre-strict-evas-${DATE_TAG}"
SUMMARY_PREFIX="results/mimo-D-strictv3-${MODEL}-${DATE_TAG}"

printf '[mimo-full] model=%s\n' "$MODEL"
printf '[mimo-full] base_url=%s\n' "$MIMO_BASE_URL"
printf '[mimo-full] generated=%s\n' "$GEN_DIR"
printf '[mimo-full] results=%s\n' "$RESULT_DIR"

python3 runners/generate.py \
  --model "$MODEL" \
  --bench-dir benchmark-balanced \
  --output-dir "$GEN_DIR" \
  --public-spec-mode spectre-strict-v3 \
  --temperature 0 \
  --top-p 1 \
  --max-tokens "$MAX_TOKENS" \
  --max-workers "$GEN_WORKERS"

python3 runners/validate_benchmark_v2_gold.py \
  --backend evas \
  --bench-dir benchmark-balanced \
  --candidate-dir "$GEN_DIR" \
  --model "$MODEL" \
  --output-dir "$RESULT_DIR" \
  --timeout-s "$TIMEOUT_S"

python3 runners/summarize_experiment_costs.py \
  --generated-dir "$GEN_DIR" \
  --bench-dir benchmark-balanced \
  --result-dir "$RESULT_DIR" \
  --output-prefix "$SUMMARY_PREFIX"

printf '[mimo-full] done\n'
printf '[mimo-full] model_results=%s/model_results.json\n' "$RESULT_DIR"
printf '[mimo-full] summary=%s.md\n' "$SUMMARY_PREFIX"
