# Run Registry

Compact registry of important EVAS runs. Raw payloads remain in local `results/`
and are intentionally not tracked.

| Date | Model | Split | Condition | Pass@1 | Source (local path) | Notes |
|---|---|---|---|---:|---|---|
| 2026-04-23 | kimi-k2.5 | full92 (repair subset) | F | 0.4348 | `results/experiment-condition-F-full92-contract-phase-rerun` | multi-round EVAS, no-skill |
| 2026-04-23 | kimi-k2.5 | dev24 (repair subset) | F | 0.4706 | `results/experiment-condition-F-full-contract-phase-rerun` | companion run |
| 2026-04-24 | kimi-k2.5 | dev24 | A | 0.2917 | `results/current-snapshot-A-kimi-k2.5-dev24` | baseline refresh |
| 2026-04-24 | kimi-k2.5 | dev24 | B | 0.2500 | `results/current-snapshot-B-kimi-k2.5-dev24` | checker-only baseline |
| 2026-04-24 | kimi-k2.5 | dev24 | C | 0.3750 | `results/current-snapshot-C-kimi-k2.5-dev24` | checker+skill baseline |
| 2026-04-24 | qwen3-max-2026-01-23 | dev24 | A | 0.2083 | `results/current-snapshot-A-qwen3-max-2026-01-23-dev24` | baseline refresh |
| 2026-04-24 | qwen3-max-2026-01-23 | dev24 | B | 0.1667 | `results/current-snapshot-B-qwen3-max-2026-01-23-dev24` | checker-only baseline |
| 2026-04-24 | qwen3-max-2026-01-23 | dev24 | C | 0.1667 | `results/current-snapshot-C-qwen3-max-2026-01-23-dev24` | checker+skill baseline |
| 2026-04-24 | kimi-k2.5 | hard34 validation subset | F/P3 | 0.0294 | `results/evas-scoring-condition-F-kimi-k2.5-p3-hard34-2026-04-24` | observable-contract + diagnosis translation; unchanged aggregate vs P0, pass moved from `cppll_tracking_smoke` to `adpll_lock_smoke` |
| 2026-04-24 | kimi-k2.5 | hard34 validation subset | F/P4 | 0.0588 | `results/evas-scoring-condition-F-kimi-k2.5-p4-policy-hard34-2026-04-24` | repair policy v1: conservative patch prompt + closeness-guided best selection; PASS tasks `bbpd_data_edge_alignment_smoke`, `phase_accumulator_timer_wrap_smoke` |
