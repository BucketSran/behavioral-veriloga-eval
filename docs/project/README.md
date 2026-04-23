# Project Docs Index

This folder keeps project-level planning/status docs. It is separate from
benchmark source (`tasks/`) and tracked paper tables (`tables/`).

## Core Files

1. `PROJECT_STATUS.md`
   Current snapshot, key metrics, and next execution plan.
2. `EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md`
   Unified A/B/C/D/E/F definitions and cross-model comparison rules.
3. `POST_RUN_PLAYBOOK.md`
   Standard procedure after each experiment batch (status update + upload set).
4. `WORK_TODO.md`
   Longer-horizon roadmap and backlog.
5. `README_TASK_REPORT.md`
   Historical batch report and legacy verification notes.

## Ownership Rule

- `results/`: local heavy artifacts only (not tracked).
- `tables/`: compact tracked experiment conclusions.
- `docs/project/`: method definition, status, and execution planning docs.
