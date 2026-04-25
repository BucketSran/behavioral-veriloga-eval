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
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | A | 0.2717 | `results/evas-scoring-condition-A-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | raw prompt baseline |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | B | 0.2609 | `results/evas-scoring-condition-B-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | checker contract baseline; lower than A |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | C | 0.2717 | `results/evas-scoring-condition-C-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | checker + skill baseline |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | D | 0.3152 | `results/evas-scoring-condition-D-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | one-round EVAS repair, no skill; best valid qwen result in this run |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | E | 0.2826 | `results/evas-scoring-condition-E-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | one-round EVAS repair + skill |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | F | 0.3043 | `results/evas-scoring-condition-F-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | three-round EVAS repair, no skill |
| 2026-04-25 | qwen3-max-2026-01-23 | full92 | G | 0.2717 | `results/evas-scoring-condition-G-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | rate-limit contaminated; do not compare as a clean model result |
| 2026-04-25 | kimi-k2.5 | 12-task contract validation | A | 0.1667 | `results/contract-validation-condition-A-kimi-k2.5-2026-04-25` | stricter public prompt contract; A stayed `2/12` |
| 2026-04-25 | kimi-k2.5 | 12-task contract validation | B | 0.1667 | `results/contract-validation-condition-B-kimi-k2.5-2026-04-25` | stricter public prompt contract; B stayed `2/12` but DUT compile failures dropped from old B `4` to new B `2` on this subset |
| 2026-04-25 | kimi-k2.5 | single-task F probe | F | 1.0000 | `results/f-repair-settling-gray-final-v2-kimi-2026-04-25` | `gray_counter_4b_smoke` PASS after reset-hold repair and clocked-output settling override `tedge=10p` |
| 2026-04-25 | kimi-k2.5 | 16-task hard small matrix | F latest policy | 0.2500 | `results/f-smallmatrix-kimi-latest-policy-strict-2026-04-25` | Standard F runner with latest skeletons: `4/16` PASS. Matches old full92 F on this subset but underperforms adaptive layered-only `9/16`; main bottleneck remains behavior repair and occasional compile regression. |
| 2026-04-25 | kimi-k2.5 | 16-task hard small matrix | F + layered-only | 0.3125 | `results/f-layered-smallmatrix-kimi-strict-2026-04-25` | Main F runner with `--layered-only-repair`: `5/16` PASS. Gains `comparator_hysteresis_smoke` and `dac_binary_clk_4b_smoke`, preserves `gray_counter_4b_smoke`, but still trails standalone adaptive layered-only `9/16`. |
| 2026-04-25 | kimi-k2.5 | 16-task hard small matrix | adaptive v3 latest standalone | 0.3750 | `results/adaptive-smallmatrix-kimi-skeleton-v3-2026-04-25` | `6/16` PASS. More recent skeletons did not monotonically improve the single trajectory; this exposed candidate-regression and forgotten-success issues. |
| 2026-04-25 | kimi-k2.5 | 10-task hard continuation | adaptive v4 patience=2 | 0.2000 | `results/adaptive-smallmatrix-kimi-skeleton-v4-continue-2026-04-25` | `2/10` PASS on v3 failures: recovered `cppll_tracking_smoke` and `sample_hold_droop_smoke`, showing behavior-layer patience can help. |
| 2026-04-25 | kimi-k2.5 | 7-task targeted hard subset | adaptive v5 anchor guard | 0.1429 | `results/adaptive-smallmatrix-kimi-skeleton-v5-anchor-guard-2026-04-25` | `1/7` PASS on targeted failures: recovered `serializer_8b_smoke`; added best-so-far anchor guard so regressed candidates do not become the next repair base. |
| 2026-04-25 | kimi-k2.5 | 16-task hard small matrix | adaptive v6 candidate memory | 0.6875 | `results/adaptive-smallmatrix-kimi-skeleton-v6-memory-2026-04-25` | `11/16` PASS. Selects best round-0 candidate from prior EVAS-verified roots, then repairs only remaining failures. This is the best current Hard16 method-development result, but not a clean A/B/C/D/E/F/G condition. |
| 2026-04-25 | kimi-k2.5 | 5-task remaining hard subset | adaptive v7 structural skeletons | 0.2000 | `results/adaptive-smallmatrix-kimi-skeleton-v7-structural-2026-04-25` | `1/5` PASS on remaining failures: `dwa_ptr_gen_smoke`. Added complex submodule local-validation, multi-module interface/harness sanity, and PFD/PLL timing-window skeletons. |
| 2026-04-25 | kimi-k2.5 | 4-task remaining hard subset | adaptive v8 runtime-interface routing | 0.0000 | `results/adaptive-smallmatrix-kimi-skeleton-v8-runtime-interface-2026-04-25` | No new PASS, but `sar_adc_dac_weighted_8b_smoke` progressed from `tran.csv missing` to behavior metrics: `unique_codes=1`, `vout_span=0.000`. |
| 2026-04-25 | kimi-k2.5 | 16-task hard small matrix | adaptive v10 memory summary | 0.7500 | `results/adaptive-smallmatrix-kimi-skeleton-v10-memory-summary-2026-04-25` | `12/16` PASS by merging v6/v7/v8/v9 best candidates. Remaining failures: ADPLL behavior ratio, gain runtime CSV, PFD checker timeout, SAR stuck code path. |
| 2026-04-25 | kimi-k2.5 | A-failed ∩ Hard16 | adaptive v10 policy reuse | 0.8000 | `results/a-failed-hard16-kimi-v10policy-2026-04-25` | `12/15` PASS when starting from condition-A failures and allowing v10 EVAS-verified candidates. This is an in-domain rescue check, not a held-out generalization result. Remaining: `adpll_timer_smoke`, `pfd_reset_race_smoke`, `sar_adc_dac_weighted_8b_smoke`. |
| 2026-04-25 | kimi-k2.5 | A-failed non-Hard16 heldout20 | adaptive layered repair | 0.3000 | `results/a-failed-heldout20-kimi-layered-v10policy-2026-04-25` | `6/20` PASS without Hard16 candidate memory. `10/20` tasks progressed by failure layer; strong on compile/interface/simple behavior, weak on PLL/crossing/divider timing and checker-timeout behaviors. |
