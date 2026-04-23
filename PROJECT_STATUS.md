# Project Status

Last updated: 2026-04-24

## 1) Project Goal

Build a model-agnostic EVAS closed-loop evaluation workflow for behavioral
Verilog-A generation and repair, then compare conditions `A/B/C/D/E/F` across
models under a consistent benchmark protocol.

## 2) Current Benchmark Scope

- Total tasks: `92`
- Families:
  - `end-to-end`: 55
  - `spec-to-va`: 18
  - `bugfix`: 8
  - `tb-generation`: 11

## 3) Current Snapshot (Tracked Summary)

Main condition definitions:
- `A`: raw baseline (no checker, no skill, no EVAS)
- `B`: checker-visible baseline
- `C`: checker + skill baseline
- `D`: single-round EVAS repair (no skill)
- `E`: single-round EVAS repair (with skill)
- `F`: three-round EVAS repair (no skill)

Reference:
- `EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md`

Key recorded runs:
- `kimi-k2.5`, `F`, full92 repair subset: `0.4348`
- `kimi-k2.5`, `F`, dev24 repair subset: `0.4706`
- dev24 baseline refresh:
  - `kimi`: `A=0.2917`, `B=0.2500`, `C=0.3750`
  - `qwen3-max-2026-01-23`: `A=0.2083`, `B=0.1667`, `C=0.1667`

Reference:
- `tables/RUN_REGISTRY.md`

## 4) Where To Look First (5-Minute Onboarding)

1. `README.md` — project overview and core workflow
2. `EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md` — official A-F protocol
3. `runners/run_experiment_matrix.py` — experiment execution entry
4. `tables/` — tracked paper-facing table summaries
5. `docs/EXPERIMENT_ASSET_POLICY.md` — what to keep/push after each run

## 5) Storage and Versioning Policy (Current)

- Raw heavy artifacts remain local under `results/` (ignored by git).
- Tracked conclusions are stored under `tables/`.
- Source-of-truth code and benchmark definitions:
  - `tasks/`, `runners/`, `scripts/`, `schemas/`, `tests/`.

## 6) Next Execution Plan

1. Complete full92 `A/B/C` for `kimi` and `qwen` under the same snapshot.
2. Complete dev24 `D/E/F` for `qwen`.
3. Promote stable repair conditions to full92 (`D/F`) for both models.
4. Refresh `tables/` and append run lines into `tables/RUN_REGISTRY.md`.
