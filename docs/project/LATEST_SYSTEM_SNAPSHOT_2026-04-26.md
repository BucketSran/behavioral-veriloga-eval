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

## Refreshed Kimi A-H Matrix

These runs re-score existing Kimi artifacts with the latest EVAS/checker system.
They do not call the LLM again. `A/B/C` use `score.py`; `D/E/F/G` use
`score_repair_artifacts.py` to select the best observed repair round. `H` is
reported separately because it is currently a DUT-side repair prototype using
the benchmark gold/reference harness, not a full generated-testbench formal
condition.

| Condition | Result dir | Pass@1 | Pass count | Notes |
|---|---|---:|---:|---|
| `A` | `results/latest-system-score-condition-A-kimi-2026-04-26` | 0.1957 | 18/92 | Raw prompt artifact. |
| `B` | `results/latest-system-score-condition-B-kimi-2026-04-26` | 0.2717 | 25/92 | Checker-transparent artifact. |
| `C` | `results/latest-system-score-condition-C-kimi-2026-04-26` | 0.2717 | 25/92 | Checker + Skill artifact. |
| `D` | `results/latest-system-score-condition-D-bestround-kimi-2026-04-26` | 0.5217 | 48/92 | Single-round EVAS, no Skill. |
| `E` | `results/latest-system-score-condition-E-bestround-kimi-2026-04-26` | 0.5109 | 47/92 | Single-round EVAS + Skill. |
| `F` | `results/latest-system-score-condition-F-bestround-kimi-2026-04-26-stable` | 0.6304 | 58/92 | Multi-round EVAS, no Skill; stable scorer config. |
| `G` | `results/latest-system-score-condition-G-bestround-kimi-2026-04-26` | 0.5326 | 49/92 | Multi-round EVAS + Skill. |
| `H` | `results/latest-system-score-condition-H-on-F-kimi-2026-04-26-stable` | 0.6413 | 59/92 | Formal H-on-F: F best-round artifacts plus H rescued DUT replacements. |

Family rates:

| Condition | End-to-end | Spec-to-VA | Bugfix | TB generation |
|---|---:|---:|---:|---:|
| `A` | 0.0909 | 0.1667 | 0.5000 | 0.5455 |
| `B` | 0.1636 | 0.2778 | 0.6250 | 0.5455 |
| `C` | 0.1455 | 0.2778 | 0.7500 | 0.5455 |
| `D` | 0.4182 | 0.4444 | 0.7500 | 1.0000 |
| `E` | 0.4182 | 0.4444 | 0.6250 | 1.0000 |
| `F` | 0.5636 | 0.5556 | 0.7500 | 1.0000 |
| `G` | 0.4545 | 0.3889 | 0.7500 | 1.0000 |
| `H` | 0.5636 | 0.6111 | 0.7500 | 1.0000 |

Failure taxonomy:

| Condition | `FAIL_SIM_CORRECTNESS` | `FAIL_DUT_COMPILE` | `FAIL_TB_COMPILE` | `FAIL_OTHER` |
|---|---:|---:|---:|---:|
| `A` | 48 | 20 | 5 | 1 |
| `B` | 43 | 18 | 5 | 1 |
| `C` | 41 | 19 | 5 | 2 |
| `D` | 41 | 1 | 0 | 2 |
| `E` | 39 | 3 | 1 | 2 |
| `F` | 31 | 1 | 0 | 2 |
| `G` | 38 | 3 | 0 | 2 |
| `H` | 30 | 1 | 0 | 2 |

## Repair Conditions Notes

`D/E/F/G` historical full92 Kimi results exist, but they were produced before
the latest DFF checker-window fix and before the final signature-H framing.
They remain useful for trend reading, but the refreshed table above should be
treated as the current Kimi formal snapshot.

| Condition | Historical result | Pass@1 | Pass count | Refresh status |
|---|---|---:|---:|---|
| `D` | `results/evas-scoring-condition-D-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5000 | 46/92 | Latest refresh is 48/92. |
| `E` | `results/evas-scoring-condition-E-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.4891 | 45/92 | Latest refresh is 47/92. |
| `F` | `results/evas-scoring-condition-F-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5761 | 53/92 | Latest stable refresh is 58/92. |
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
- Key observation before H materialization: `F` is the strongest A-G formal
  Kimi condition. Under the stable scorer config it reaches `58/92`, while `G`
  remains lower. Skill injection is not automatically beneficial in the current
  repair loop and may introduce less compatible implementation choices.

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
| Formal H-on-F materialization | 92 | 3 applied | 59 formal PASS | +1 over F-stable |

H accounting over the 41 historical G-failed Kimi tasks:

| Bucket | Count | Meaning |
|---|---:|---|
| Re-scored G already PASS | 10 | Not H rescues; latest checker/scoring says the existing artifact passes. |
| Strict H rescues | 3 | H repaired a failing DUT-side G anchor to PASS. |
| H eligible but no rescue needed | 1 | `dff_rst_smoke` passes after the DFF checker-window fix. |
| Still unresolved | 28 | H did not apply a trusted template or could not get enough diagnostic evidence. |

Formal H materialization:

- Script: `runners/materialize_condition_h.py`
- Base: `generated-table2-evas-guided-repair-3round` with
  `results/latest-system-score-condition-F-bestround-kimi-2026-04-26-stable`
- H summaries:
  `results/signature-guided-H-Gfailed-eligible4-fixed-checker-2026-04-26`
- Output generated tree:
  `generated-condition-H-on-F-kimi-2026-04-26`
- Formal score:
  `results/latest-system-score-condition-H-on-F-kimi-2026-04-26-stable`

Formal delta against the same stable F scoring config:

| Comparison | Pass count | Delta |
|---|---:|---:|
| `F-stable` | 58/92 | baseline |
| `H-on-F-stable` | 59/92 | +1 |

The only formal gain over `F-stable` is:

| Task | F-stable | H-on-F-stable | Why it improves |
|---|---|---|---|
| `multimod_divider` | `FAIL_SIM_CORRECTNESS`, `base=4 pre_count=4 post_count=4` | `PASS`, `base=4 pre_count=9 post_count=9` | H replaces the DUT with a signature-gated multimod cadence template. |

Strict H rescues:

| Task | Failure signature | Template family | Best variant |
|---|---|---|---|
| `clk_divider` | `cadence_ratio_hist` | `counter_cadence_programmable_divider` | `segment_ceil_low_floor_high` |
| `multimod_divider` | `cadence_multimod_counts` | `counter_cadence_multimod_prescaler` | `pulse_every_base_or_base_plus_one_reset0` |
| `flash_adc_3b_smoke` | `quantizer_code_coverage` | `clocked_quantizer_code_coverage` | `clocked_uniform_3b_quantizer` |

`dff_rst_smoke` is not counted as an H rescue because the latest checker fix
makes the re-scored G baseline pass.

`flash_adc_3b_smoke` is a DUT-side H rescue, but it does not become a formal
end-to-end pass after materialization. The generated testbench still produces
`too_few_edges=0`, so the corrected DUT is not properly exercised.

Why the remaining H cases are not fixed yet:

| Failure bucket | Example | EVAS note | Why H does not repair it yet |
|---|---|---|---|
| Timeout-only / weak diagnostic | `pfd_deadzone_smoke` | `behavior_eval_timeout>26s` | No pulse-width or phase-window metrics are available, so the PFD template cannot safely choose a repair. |
| Timeout / expensive harness | `pfd_reset_race_smoke` | `evas_timeout>80s` | The baseline harness times out before H gets useful behavior notes; this needs runtime/checker optimization first. |
| Interface/template mismatch | `dwa_ptr_gen_no_overlap_smoke` | `evas_timeout>80s`; onehot signature detected | The anchor exposes bus-style ports (`cell_en_o`, `ptr_o`) while the older exploratory DWA template assumes scalar-expanded ports; applying it would risk interface breakage. |
| Complex system behavior | `adpll_ratio_hop_smoke` | `pre_ratio=8.000 post_ratio=8.000 pre_lock=0.000 post_lock=0.000` | This is a system-level PLL behavior failure. Current H has no safe submodule decomposition or lock/reacquire template. |
| Complex system behavior | `cppll_tracking_smoke` | `freq_ratio=1.0889 fb_jitter_frac=0.0446 lock_time=nan` | Requires PLL loop/timing-window reasoning, not a simple local counter or quantizer skeleton. |
| Missing activity | `cdac_cal` | `no vdac activity` | H lacks a CDAC calibration/output-activity template and should first localize whether the issue is code update, DAC output, or harness observability. |
| No output cadence/activity | `multimod_divider_ratio_switch_smoke` | `not_enough_edges in=320 out=0` | The existing multimod template only covers `base/pre_count/post_count`; this case needs a startup/output-enable cadence template. |
| Sequence stuck | `nrz_prbs` | `transitions=0 complement_err=0.0041 swing=0.900` | Needs a PRBS/LFSR sequence-state template; current H has not promoted that family. |
| Checker/runtime timeout | `bad_bus_output_loop` | `behavior_eval_timeout>26s` | Current notes do not identify whether the issue is bus indexing, save policy, or behavior, so H refuses to guess. |
| Compile or harness failure | `digital_basics_smoke` | `tb_not_executed`, `tran.csv missing` | H is currently DUT-side behavior repair; compile/TB linkage must be fixed before behavior templates are useful. |
| Non-single-module artifact | `segmented_dac` | `Cannot find a parseable single-module anchor` | H currently requires a parseable single-module DUT anchor. Multi-module/local-submodule H is still future work. |

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
