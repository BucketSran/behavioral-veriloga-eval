# Latest System Snapshot

Date: 2026-04-26

This note records which results have been refreshed after the latest scoring
system changes:

- per-task EVAS output isolation for parallel scoring
- `--resume` fingerprinted scoring cache
- `--save-policy contract`
- experimental streaming checkers disabled by default
- DFF checker sampling-window fix
- signature-gated condition-H prototype

## Refreshed Kimi A-G Formal Matrix

These runs re-score existing Kimi artifacts with the latest EVAS/checker system.
They do not call the LLM again. `A/B/C` use `score.py`; `D/E/F/G` use
`score_repair_artifacts.py` to select the best observed repair round.

| Condition | Result dir | Pass@1 | Pass count | Notes |
|---|---|---:|---:|---|
| `A` | `results/latest-system-score-condition-A-kimi-2026-04-26` | 0.1957 | 18/92 | Raw prompt artifact. |
| `B` | `results/latest-system-score-condition-B-kimi-2026-04-26` | 0.2717 | 25/92 | Checker-transparent artifact. |
| `C` | `results/latest-system-score-condition-C-kimi-2026-04-26` | 0.2717 | 25/92 | Checker + Skill artifact. |
| `D` | `results/latest-system-score-condition-D-bestround-kimi-2026-04-26` | 0.5217 | 48/92 | Single-round EVAS, no Skill. |
| `E` | `results/latest-system-score-condition-E-bestround-kimi-2026-04-26` | 0.5109 | 47/92 | Single-round EVAS + Skill. |
| `F` | `results/latest-system-score-condition-F-bestround-kimi-2026-04-26` | 0.6087 | 56/92 | Multi-round EVAS, no Skill. |
| `G` | `results/latest-system-score-condition-G-bestround-kimi-2026-04-26` | 0.5326 | 49/92 | Multi-round EVAS + Skill. |

Family rates:

| Condition | End-to-end | Spec-to-VA | Bugfix | TB generation |
|---|---:|---:|---:|---:|
| `A` | 0.0909 | 0.1667 | 0.5000 | 0.5455 |
| `B` | 0.1636 | 0.2778 | 0.6250 | 0.5455 |
| `C` | 0.1455 | 0.2778 | 0.7500 | 0.5455 |
| `D` | 0.4182 | 0.4444 | 0.7500 | 1.0000 |
| `E` | 0.4182 | 0.4444 | 0.6250 | 1.0000 |
| `F` | 0.5273 | 0.5556 | 0.7500 | 1.0000 |
| `G` | 0.4545 | 0.3889 | 0.7500 | 1.0000 |

Failure taxonomy:

| Condition | `FAIL_SIM_CORRECTNESS` | `FAIL_DUT_COMPILE` | `FAIL_TB_COMPILE` | `FAIL_OTHER` |
|---|---:|---:|---:|---:|
| `A` | 48 | 20 | 5 | 1 |
| `B` | 43 | 18 | 5 | 1 |
| `C` | 41 | 19 | 5 | 2 |
| `D` | 41 | 1 | 0 | 2 |
| `E` | 39 | 3 | 1 | 2 |
| `F` | 33 | 1 | 0 | 2 |
| `G` | 38 | 3 | 0 | 2 |

## Repair Conditions Notes

`D/E/F/G` historical full92 Kimi results exist, but they were produced before
the latest DFF checker-window fix and before the final signature-H framing.
They remain useful for trend reading, but the refreshed table above should be
treated as the current Kimi formal snapshot.

| Condition | Historical result | Pass@1 | Pass count | Refresh status |
|---|---|---:|---:|---|
| `D` | `results/evas-scoring-condition-D-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5000 | 46/92 | Latest refresh is 48/92. |
| `E` | `results/evas-scoring-condition-E-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.4891 | 45/92 | Latest refresh is 47/92. |
| `F` | `results/evas-scoring-condition-F-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5761 | 53/92 | Latest refresh is 56/92. |
| `G` | `results/evas-scoring-condition-G-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5543 | 51/92 | Latest refresh is 49/92. |

Important G refresh observation:

- On the 41 historical G-failed tasks, the latest report-only re-score found 10
  tasks that now pass.
- The formal generated-testbench best-round refresh on all 92 tasks gives
  `49/92`, so the report-only DUT/gold-harness observation should not be
  interpreted as the formal end-to-end G number.

Repair-artifact scorer status:

- Added `runners/score_repair_artifacts.py` to re-score all available
  `sample_0` / `sample_0_roundN` directories and select the best observed round.
- A smoke on `clk_divider`, `dff_rst_smoke`, and `flash_adc_3b_smoke` under the
  formal generated-testbench path produced `0/3` pass.
- This differs from H because current H uses the gold/reference harness for
  DUT-side behavior repair. The distinction is intentional and must be kept
  explicit in claims.
- Key observation: `F` is currently the strongest formal Kimi condition
  (`56/92`), while `G` drops to `49/92`. Skill injection is not automatically
  beneficial in the current repair loop and may introduce less compatible
  implementation choices.

## Current H Evidence

Condition H is now:

`G + EVAS failure signature + module/interface signature + bounded template candidates + EVAS fitness selection`

Current H scope:

- DUT-side repair with the benchmark gold/reference testbench.
- Not yet a full end-to-end generated-testbench closure result.

Latest H evidence:

| Run | Tasks | Eligible | Best pass | Strict rescues |
|---|---:|---:|---:|---:|
| G-failed report-only sweep | 41 | 4 | 10 re-scored G PASS | 0 |
| Eligible-4 H repair | 4 | 4 | 4 | 3 |

Strict H rescues:

| Task | Failure signature | Template family | Best variant |
|---|---|---|---|
| `clk_divider` | `cadence_ratio_hist` | `counter_cadence_programmable_divider` | `segment_ceil_low_floor_high` |
| `multimod_divider` | `cadence_multimod_counts` | `counter_cadence_multimod_prescaler` | `pulse_every_base_or_base_plus_one_reset0` |
| `flash_adc_3b_smoke` | `quantizer_code_coverage` | `clocked_quantizer_code_coverage` | `clocked_uniform_3b_quantizer` |

`dff_rst_smoke` is not counted as an H rescue because the latest checker fix
makes the re-scored G baseline pass.

## Refreshed Qwen A-G Formal Matrix

These are the matching latest-system scores for `qwen3-max-2026-01-23`.

| Condition | Result dir | Pass@1 | Pass count | Notes |
|---|---|---:|---:|---|
| `A` | `results/latest-system-score-condition-A-qwen-2026-04-26` | 0.2717 | 25/92 | Raw prompt artifact. |
| `B` | `results/latest-system-score-condition-B-qwen-2026-04-26` | 0.2500 | 23/92 | Checker-transparent artifact. |
| `C` | `results/latest-system-score-condition-C-qwen-2026-04-26` | 0.2717 | 25/92 | Checker + Skill artifact. |
| `D` | `results/latest-system-score-condition-D-bestround-qwen-2026-04-26` | 0.3043 | 28/92 | Single-round EVAS, no Skill. |
| `E` | `results/latest-system-score-condition-E-bestround-qwen-2026-04-26` | 0.2717 | 25/92 | Single-round EVAS + Skill. |
| `F` | `results/latest-system-score-condition-F-bestround-qwen-2026-04-26` | 0.2935 | 27/92 | Multi-round EVAS, no Skill. |
| `G` | `results/latest-system-score-condition-G-bestround-qwen-2026-04-26` | 0.2500 | 23/92 | Multi-round EVAS + Skill; artifact quality needs review. |

Family rates:

| Condition | End-to-end | Spec-to-VA | Bugfix | TB generation |
|---|---:|---:|---:|---:|
| `A` | 0.1091 | 0.2222 | 0.6250 | 0.9091 |
| `B` | 0.0909 | 0.1667 | 0.7500 | 0.8182 |
| `C` | 0.1091 | 0.2778 | 0.5000 | 0.9091 |
| `D` | 0.1273 | 0.2778 | 0.8750 | 0.8182 |
| `E` | 0.1091 | 0.1667 | 0.8750 | 0.8182 |
| `F` | 0.1273 | 0.2222 | 0.8750 | 0.8182 |
| `G` | 0.0909 | 0.1667 | 0.7500 | 0.8182 |

Key Qwen observations:

- Qwen does not show the large Kimi-style closed-loop lift. Best refreshed Qwen
  condition is `D` at `28/92`.
- Qwen failures are much more compile/TB-heavy in `A/B/C`, so EVAS behavioral
  repair has less room to help unless compile/harness stability improves first.
- Qwen `G` contains many generated repair artifacts that score as infra or
  compile failures. Treat this as an artifact-quality warning before using it
  for strong model comparisons.

## Next Refresh Work

1. Decide whether to re-run LLM generation for A/B/C if prompt files changed
   materially since the stored artifacts were generated.
2. Inspect Qwen `G` repair artifacts to distinguish real model limitation from
   generated artifact/runner incompleteness.
3. Decide whether H should be evaluated first on Kimi only, or also run on a
   small Qwen subset after artifact quality is checked.
