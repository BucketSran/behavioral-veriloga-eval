# MiMo Full-Run Plan

This plan runs the unified `D` condition on `benchmark-balanced` with Xiaomi MiMo.

## Condition

- Benchmark: `benchmark-balanced` full 143 tasks.
- Model: `mimo-v2.5-pro`.
- Prompt condition: `D = spectre-strict-v3`, one-shot generation, no repair.
- Validator: spectre-strict EVAS through `runners/validate_benchmark_v2_gold.py --candidate-dir ... --bench-dir benchmark-balanced`.
- Accounting: `generation_meta.json` plus `summarize_experiment_costs.py` grouped tables.

## Command

Set `MIMO_API_KEY` in the shell, then run:

```bash
MIMO_API_KEY=... runners/run_mimo_d_full.sh
```

Optional knobs:

```bash
MODEL=mimo-v2.5-pro
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
GEN_WORKERS=2
MAX_TOKENS=4096
TIMEOUT_S=240
DATE_TAG=2026-05-04
```

## Expected Artifacts

- Generated root: `generated-balanced-D-strictv3-mimo-v2.5-pro-2026-05-04`
- Result root: `results/balanced-D-strictv3-mimo-v2.5-pro-spectre-strict-evas-2026-05-04`
- Cost summary: `results/mimo-D-strictv3-mimo-v2.5-pro-2026-05-04.md`

## Follow-Up Decision

After the full `D` row:

1. If compile failures dominate, run `C-SKILL` / `C-ULTRA` on MiMo-D candidates.
2. If compile is clean but behavior is weak, run public-only `G0` mechanism guidance.
3. Only run `F` or `I` after the D failure distribution is clear.
