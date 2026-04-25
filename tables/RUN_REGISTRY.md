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
| 2026-04-25 | kimi-k2.5 | full92 | A | 0.3804 | `results/evas-scoring-condition-A-kimi-k2.5-full86-2026-04-25-overnight-kimi` | raw prompt baseline |
| 2026-04-25 | kimi-k2.5 | full92 | B | 0.4674 | `results/evas-scoring-condition-B-kimi-k2.5-full86-2026-04-25-overnight-kimi` | checker contract baseline |
| 2026-04-25 | kimi-k2.5 | full92 | C | 0.4022 | `results/evas-scoring-condition-C-kimi-k2.5-full86-2026-04-25-overnight-kimi` | checker + skill baseline |
| 2026-04-25 | kimi-k2.5 | full92 | D | 0.5000 | `results/evas-scoring-condition-D-kimi-k2.5-full86-2026-04-25-overnight-kimi` | one-round EVAS repair, no skill |
| 2026-04-25 | kimi-k2.5 | full92 | E | 0.4891 | `results/evas-scoring-condition-E-kimi-k2.5-full86-2026-04-25-overnight-kimi` | one-round EVAS repair + skill |
| 2026-04-25 | kimi-k2.5 | full92 | F | 0.5761 | `results/evas-scoring-condition-F-kimi-k2.5-full86-2026-04-25-overnight-kimi` | three-round EVAS repair, no skill; best current full92 result |
| 2026-04-25 | kimi-k2.5 | full92 | G | 0.5543 | `results/evas-scoring-condition-G-kimi-k2.5-full86-2026-04-25-overnight-kimi` | three-round EVAS repair + skill; missing generated samples counted as failures |
