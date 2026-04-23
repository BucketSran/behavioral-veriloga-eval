# Post-Run Playbook

This checklist standardizes what to keep locally, what to track in git, and
how to refresh project status after each experiment batch.

## 1) Run Completion Gate (Local)

1. Confirm the batch finished (no pending jobs, no partial folder writes).
2. Verify key outcomes from local `results/<run_name>/`:
   - summary json/csv exists
   - pass/fail counts are internally consistent
   - failure reasons are parseable (not infra-noise only)
3. If run quality is poor because of infra issues, mark as invalid and rerun
   before updating tracked docs.

## 2) Update Tracked Tables

1. Sync table files:

```bash
scripts/sync_tables_from_results.sh
```

2. Update `tables/RUN_REGISTRY.md` with one row per important run:
   - date
   - model
   - split (`dev24` / `full92`)
   - condition (`A`..`F`)
   - Pass@1
   - source local path under `results/`
   - short notes

## 3) Update Project Status

Update these files in order:

1. `docs/project/PROJECT_STATUS.md`
   - current tracked snapshot
   - next execution plan
2. `docs/project/WORK_TODO.md`
   - progress state for roadmap items
   - newly observed blockers or policy adjustments

## 4) Upload Scope (What To Commit)

Commit and push:

- source changes:
  - `tasks/**`
  - `runners/**`
  - `scripts/**`
  - `tests/**` (if changed)
- project docs:
  - `docs/project/**`
  - `docs/EXPERIMENT_ASSET_POLICY.md` (if changed)
- tracked summaries:
  - `tables/**`

Do not commit:

- `results/**`
- `generated-*` run payload folders
- per-sample intermediates (`repair_prompt.md`, `result.json`, `tran.csv`, ...)

## 5) Minimal End-Of-Run Deliverable

A run batch is considered "closed" only when all items below are complete:

1. local raw results are present and interpretable;
2. `tables/` and `tables/RUN_REGISTRY.md` are refreshed;
3. `docs/project/PROJECT_STATUS.md` reflects the latest state;
4. commit message clearly indicates model/split/condition coverage.
