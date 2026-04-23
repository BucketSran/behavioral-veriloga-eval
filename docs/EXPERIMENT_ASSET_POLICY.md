# Experiment Asset Policy

This file defines what to keep after each experiment and what to upload to
remote to keep the repo small and easy to navigate.

## What Must Be Tracked (push to remote)

- benchmark source changes
  - `tasks/**/prompt.md`
  - `tasks/**/meta.json`
  - `tasks/**/checks.yaml`
  - task-level `gold/` files only when benchmark truth is updated
- experiment method code
  - `runners/**` and `scripts/**` that change how experiments run
- experiment plan and condition definitions
  - `EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md`
- paper-facing result summaries
  - `tables/` (Table 1 / Table 2 summaries and failure analysis)

## What Must Stay Local (do not push)

- raw run payloads
  - `results/**` (ignored by default)
  - `generated-table2*/`, `generated-experiment/`, `generated-loop*/`
- per-sample intermediate files
  - `repair_prompt.md`
  - `generation_meta.json`
  - `result.json`
  - `tran.csv`

## End-Of-Run Checklist

After each experiment batch:

1. Verify result quality in local `results/`.
2. Update or regenerate `tables/` summaries.
3. Append one line to `tables/RUN_REGISTRY.md`.
4. Commit only:
   - source changes (`tasks/`, `runners/`, `scripts/`)
   - plan docs
   - `tables/`
5. Delete local bulky generated folders if no longer needed.

## One-Line Rule

Remote should keep only reproducible methodology and compact conclusions; local
disk keeps heavy artifacts.
