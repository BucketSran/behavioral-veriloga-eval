# Tables (Tracked)

This directory keeps paper-facing table/result summaries that should be tracked
by git.

Why this exists:
- `results/` is ignored by `.gitignore` for large payload control.
- Important summary tables under `results/` would otherwise not be versioned.

Current tracked table files:
- `TABLE1_EVAS_VS_SPECTRE_GOLD.md`
- `TABLE2_SUMMARY.md`
- `TABLE2_FAILURE_ANALYSIS.md`
- `RUN_REGISTRY.md`

Source of these files:
- copied from `results/` on 2026-04-24 to preserve important conclusions in a
  tracked location.

Update rule:
1. refresh table content in `results/` after experiments
2. copy updated summaries into `tables/`
3. commit only the tracked `tables/` files for remote sharing

Helper:
- `scripts/sync_tables_from_results.sh`
  - syncs table summaries from local `results/` into this tracked folder
