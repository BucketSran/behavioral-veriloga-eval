# Project Status

Last updated: 2026-04-25

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
- `docs/project/EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md`

Key recorded runs:
- `kimi-k2.5`, `F`, full92 repair subset: `0.4348`
- `kimi-k2.5`, `F`, dev24 repair subset: `0.4706`
- dev24 baseline refresh:
  - `kimi`: `A=0.2917`, `B=0.2500`, `C=0.3750`
  - `qwen3-max-2026-01-23`: `A=0.2083`, `B=0.1667`, `C=0.1667`

Reference:
- `tables/RUN_REGISTRY.md`

Latest local adaptive-repair status:
- The current focus has shifted from running more `A/B/C/D/E/F` matrix cells to improving the EVAS
  repair loop itself.
- Two reusable observable-layer skeletons have been implemented locally:
  - `observable_scalar_alias_template`
  - `post_reset_sample_budget_template`
- These skeletons do not yet improve final Pass@1 directly, but they convert shallow observable
  failures into behavior-level EVAS diagnostics.

Reference:
- `docs/project/ADAPTIVE_REPAIR_SKELETON_STATUS.md`

## 4) Where To Look First (5-Minute Onboarding)

1. `README.md` — project overview and core workflow
2. `docs/project/EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md` — official A-F protocol
3. `runners/run_experiment_matrix.py` — experiment execution entry
4. `tables/` — tracked paper-facing table summaries
5. `docs/EXPERIMENT_ASSET_POLICY.md` — what to keep/push after each run
6. `docs/project/POST_RUN_PLAYBOOK.md` — post-run update/upload checklist
7. `docs/project/ADAPTIVE_REPAIR_SKELETON_STATUS.md` — latest adaptive repair skeleton status

## 5) Storage and Versioning Policy (Current)

- Raw heavy artifacts remain local under `results/` (ignored by git).
- Tracked conclusions are stored under `tables/`.
- Source-of-truth code and benchmark definitions:
  - `tasks/`, `runners/`, `scripts/`, `schemas/`, `tests/`.

## 6) Next Execution Plan

1. Finish behavior-layer repair skeletons on the small validation set:
   - DWA pointer/count/window behavior.
   - sample-hold droop behavior.
2. Re-run the 16-task Kimi small matrix only after small-case behavior skeletons show actual PASS
   uplift or clear failure-surface progress.
3. Promote the method to the full 92-task EVAS-only experiment only after the small matrix improves.
4. Return to full `A/B/C/D/E/F` cross-model matrix runs after the repair policy is stable enough to
   justify broad comparison.
