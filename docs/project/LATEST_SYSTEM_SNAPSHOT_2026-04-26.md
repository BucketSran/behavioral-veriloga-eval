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

## Refreshed Kimi Baselines

These runs re-score existing Kimi artifacts with the latest EVAS/checker system.
They do not call the LLM again.

| Condition | Result dir | Pass@1 | Pass count | Notes |
|---|---|---:|---:|---|
| `A` | `results/latest-system-score-condition-A-kimi-2026-04-26` | 0.1957 | 18/92 | Raw prompt artifact, latest checker/save-policy. |
| `B` | `results/latest-system-score-condition-B-kimi-2026-04-26` | 0.2717 | 25/92 | Checker-transparent artifact, latest checker/save-policy. |
| `C` | `results/latest-system-score-condition-C-kimi-2026-04-26` | 0.2717 | 25/92 | Checker + Skill artifact, latest checker/save-policy. |

Family rates:

| Condition | End-to-end | Spec-to-VA | Bugfix | TB generation |
|---|---:|---:|---:|---:|
| `A` | 0.0909 | 0.1667 | 0.5000 | 0.5455 |
| `B` | 0.1636 | 0.2778 | 0.6250 | 0.5455 |
| `C` | 0.1455 | 0.2778 | 0.7500 | 0.5455 |

Failure taxonomy:

| Condition | `FAIL_SIM_CORRECTNESS` | `FAIL_DUT_COMPILE` | `FAIL_TB_COMPILE` | `FAIL_OTHER` |
|---|---:|---:|---:|---:|
| `A` | 48 | 20 | 5 | 1 |
| `B` | 43 | 18 | 5 | 1 |
| `C` | 41 | 19 | 5 | 2 |

## Repair Conditions Status

`D/E/F/G` historical full92 Kimi results exist, but they were produced before
the latest DFF checker-window fix and before the final signature-H framing.
They should remain useful for trend reading, but should not be mixed into final
paper claims without a refresh.

| Condition | Historical result | Pass@1 | Pass count | Refresh status |
|---|---|---:|---:|---|
| `D` | `results/evas-scoring-condition-D-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5000 | 46/92 | Needs latest-system rerun/rescore. |
| `E` | `results/evas-scoring-condition-E-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.4891 | 45/92 | Needs latest-system rerun/rescore. |
| `F` | `results/evas-scoring-condition-F-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5761 | 53/92 | Needs latest-system rerun/rescore. |
| `G` | `results/evas-scoring-condition-G-kimi-k2.5-full86-2026-04-25-overnight-kimi` | 0.5543 | 51/92 | Partially refreshed via G-failed report-only sweep. |

Important G refresh observation:

- On the 41 historical G-failed tasks, the latest report-only re-score found 10
  tasks that now pass.
- This does not yet constitute a full refreshed G number because only the
  historical failures were re-scored in that sweep.
- A paper-ready `G` refresh should re-score all 92 final/best G artifacts with
  the latest checker and output isolation.

Repair-artifact scorer status:

- Added `runners/score_repair_artifacts.py` to re-score all available
  `sample_0` / `sample_0_roundN` directories and select the best observed round.
- A smoke on `clk_divider`, `dff_rst_smoke`, and `flash_adc_3b_smoke` under the
  formal generated-testbench path produced `0/3` pass.
- This differs from H because current H uses the gold/reference harness for
  DUT-side behavior repair. The distinction is intentional and must be kept
  explicit in claims.

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

## Next Refresh Work

1. Add or reuse a scorer that can select the final/best round for `D/E/F/G`
   artifacts rather than only `sample_0`. Initial version:
   `runners/score_repair_artifacts.py`.
2. Re-score all 92 Kimi `D/E/F/G` final artifacts with latest checker,
   isolated outputs, and `--save-policy contract`.
3. Decide whether to re-run LLM generation for A/B/C if prompt files changed
   materially since the stored artifacts were generated.
4. Only after the Kimi refresh is stable, repeat the same refresh protocol for
   Qwen.
