# Table 2 Spectre Results Summary (2026-04-22)

## Current Status

### generic-retry (裸LLM) - dev24

| Metric | Value |
|--------|-------|
| Total | 24 tasks |
| Pass@1 | 8.33% (2/24) |
| bugfix | 33.3% (1/3) |
| spec-to-va | 20% (1/5) |
| end-to-end | 0% (0/12) |
| tb-generation | 0% (0/4) |

**Failure breakdown**: FAIL_DUT_COMPILE 14, FAIL_TB_COMPILE 4, FAIL_SIM_CORRECTNESS 3, FAIL_INFRA 1

### evas-guided-repair (EVAS闭环) - partial coverage

| Metric | Value |
|--------|-------|
| Total | 37 tasks |
| Pass@1 | 29.7% (11/37) |
| bugfix | 100% (8/8) |
| spec-to-va | 11.1% (2/18) |
| tb-generation | 9.1% (1/11) |
| end-to-end | N/A (not covered) |

**Failure breakdown**: FAIL_DUT_COMPILE 16, FAIL_TB_COMPILE 10

## Key Finding

**EVAS闭环显著提升bugfix任务性能**: 从 33.3% → 100% (提升 3x)

## Coverage Gap

evas-guided-repair 缺失 12 个 dev24 end-to-end (smoke) 任务:

```
digital_basics_smoke
lfsr_smoke
gray_counter_4b_smoke
mux_4to1_smoke
cmp_delay_smoke
comparator_hysteresis_smoke
sample_hold_smoke
dac_binary_clk_4b_smoke
adpll_ratio_hop_smoke
cppll_freq_step_reacquire_smoke
pfd_reset_race_smoke
bbpd_data_edge_alignment_smoke
```

## Overlapping Tasks Comparison (12 tasks)

| Mode | Pass |
|------|------|
| generic-retry | 2/12 (16.7%) |
| evas-guided-repair | 4/12 (33.3%) |
| **Improvement** | **+100% relative** |

Overlap tasks: sc_integrator, prbs7, clk_divider, adpll_timer, multimod_divider, inverted_comparator_logic_bug, strongarm_reset_priority_bug, wrong_edge_sample_hold_bug, sample_hold_aperture_tb, nrz_prbs_jitter_tb, comparator_offset_tb, dco_gain_step_tb

## Next Steps

1. 补充 evas-guided-repair 12 个缺失的 smoke 任务生成 (需要 BAILIAN_API_KEY)
2. 对补充后的任务进行 Spectre 评分
3. 生成完整的 Table 2 dev24 对比报告

## Raw Data Paths

- generic-retry Spectre: `results/model-spectre-eval-kimi-k2.5-table2-raw-generic-retry-dev24-2026-04-20`
- evas-guided-repair Spectre: `results/model-spectre-eval-kimi-k2.5-table2-evas-guided-repair-full86-2026-04-20`
- evas-guided-repair generated: `generated-table2-evas-guided-repair/kimi-k2.5`