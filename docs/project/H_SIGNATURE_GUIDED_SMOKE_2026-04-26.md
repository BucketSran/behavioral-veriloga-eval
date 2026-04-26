# H Signature-Guided Smoke Result

Date: 2026-04-26

## Purpose

This smoke test checks the current condition-H direction:

`G artifact -> EVAS rescore -> failure signature -> module/interface gate -> bounded template candidates -> EVAS fitness selection`

Important scope:

- The current H prototype is a DUT-side repair experiment.
- It uses the benchmark gold/reference testbench as the behavior harness.
- Therefore, H strict rescues show that EVAS-guided mechanism search can repair
  DUT behavior left unsolved by G, but they do not yet prove full end-to-end
  generated-testbench closure.

The key methodological constraint is that templates are not selected by task id.
A template may run only when the EVAS failure notes and the DUT interface both
match a reusable mechanism family.

## Report-Only Gate Check

Command:

```bash
python3 runners/signature_guided_h.py \
  --g-result-root results/runtime-profile-G-kimi-isolated-2026-04-26 \
  --anchor-root generated-table2-evas-guided-repair-3round-skill/kimi-k2.5 \
  --output-root results/signature-guided-H-report-only-smoke-2026-04-26 \
  --generated-root generated-signature-guided-H-report-only-smoke-2026-04-26 \
  --timeout-s 120 --workers 3 --resume --report-only \
  --tasks clk_divider multimod_divider flash_adc_3b_smoke dff_rst_smoke pfd_deadzone_smoke dwa_ptr_gen_no_overlap_smoke
```

Result:

| Metric | Value |
|---|---:|
| Tasks | 6 |
| Eligible | 4 |
| Unsupported | 2 |
| Rescue attempts | 0 |

Eligible families:

| Task | Failure signature | Template family |
|---|---|---|
| `clk_divider` | `cadence_ratio_hist` | `counter_cadence_programmable_divider` |
| `multimod_divider` | `cadence_multimod_counts` | `counter_cadence_multimod_prescaler` |
| `flash_adc_3b_smoke` | `quantizer_code_coverage` | `clocked_quantizer_code_coverage` |
| `dff_rst_smoke` | `sampled_latch_reset_priority` | `sampled_latch_reset_priority` |

Unsupported examples:

| Task | Why unsupported |
|---|---|
| `pfd_deadzone_smoke` | The current EVAS notes only report `behavior_eval_timeout`, so there is no reliable pulse/window signature yet. |
| `dwa_ptr_gen_no_overlap_smoke` | The current EVAS notes only report `behavior_eval_timeout`; the anchor interface is bus-style (`cell_en_o`, `ptr_o`) while the older exploratory template is scalar-expanded. |

Interpretation:

- The gate is conservative: it refuses to repair when the failure evidence is too weak or the interface does not match.
- This is desirable for avoiding task-name overfitting and accidental interface rewrites.

## Supported H Repair Smoke

Command:

```bash
python3 runners/signature_guided_h.py \
  --g-result-root results/runtime-profile-G-kimi-isolated-2026-04-26 \
  --anchor-root generated-table2-evas-guided-repair-3round-skill/kimi-k2.5 \
  --output-root results/signature-guided-H-kimi-G-supported-v2-2026-04-26 \
  --generated-root generated-signature-guided-H-kimi-G-supported-v2-2026-04-26 \
  --timeout-s 180 --workers 3 --resume \
  --tasks clk_divider multimod_divider flash_adc_3b_smoke
```

Result:

| Metric | Value |
|---|---:|
| Tasks | 3 |
| Eligible | 3 |
| Rescued | 3 |
| Unsupported | 0 |
| Best pass | 3 |

Task-level result:

| Task | G-anchor rescore | H best | Best variant | Rescue |
|---|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `segment_ceil_low_floor_high` | Yes |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `pulse_every_base_or_base_plus_one_reset0` | Yes |
| `flash_adc_3b_smoke` | `FAIL_SIM_CORRECTNESS` | `PASS` | `clocked_uniform_3b_quantizer` | Yes |

## Conclusion

This is evidence for a useful H strategy, but not yet a full92 result.

The positive result is that EVAS can select a passing candidate when the repair
space contains the right reusable mechanism. The negative result is equally
important: timeout-only failures such as current PFD/DWA anchors need better
diagnostic notes or safer checker/runtime handling before mechanism templates
should be allowed to act.

## Follow-Up: DFF Checker Sampling Fix

During the eligible-task run, `dff_rst_smoke` stayed at `q_mismatch=4`. A direct
gold check showed the same failure on `tasks/end-to-end/voltage/dff_rst_smoke/gold/dff_rst_ref.va`.

Root cause:

- The checker sampled `idx + 3` CSV rows after each clock edge.
- EVAS refinement can make those three rows only about 1.9 ps after the edge.
- The public model uses `transition(..., 10p)`, so the output is still slewing at
  that sample point.

Fix:

- `check_dff_rst` now samples by time, about 100 ps after the detected clock
  edge, and computes the expected sampled value from the edge-time `d/rst`.

Validation:

| Artifact | Before | After |
|---|---|---|
| DFF gold | `FAIL_SIM_CORRECTNESS`, `q_mismatch=4` | `PASS`, `q_mismatch=0 qb_mismatch=0` |

## G-Failed Report-Only Sweep After Checker Fix

Command:

```bash
python3 runners/signature_guided_h.py \
  --g-result-root results/runtime-profile-G-kimi-isolated-2026-04-26 \
  --anchor-root generated-table2-evas-guided-repair-3round-skill/kimi-k2.5 \
  --output-root results/signature-guided-H-report-only-Gfailed-fixed-checker-2026-04-26 \
  --generated-root generated-signature-guided-H-report-only-Gfailed-fixed-checker-2026-04-26 \
  --timeout-s 80 --workers 8 --resume --report-only
```

Result:

| Metric | Value |
|---|---:|
| Historical G-failed tasks rescored | 41 |
| Re-scored PASS | 10 |
| Eligible for H template family | 4 |
| Unsupported | 37 |

Re-scored PASS tasks:

`bbpd_data_edge_alignment_smoke`, `comparator_hysteresis_smoke`,
`dac_therm_16b_smoke`, `dac_binary_clk_4b_smoke`, `dff_rst_smoke`,
`gray_counter_one_bit_change_smoke`, `parameter_type_override_smoke`,
`sample_hold_droop_smoke`, `serializer_frame_alignment_smoke`,
`timer_absolute_grid_smoke`.

Eligible H families:

| Task | Re-scored G status | Failure signature | Template family |
|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `cadence_ratio_hist` | `counter_cadence_programmable_divider` |
| `dff_rst_smoke` | `PASS` | `sampled_latch_reset_priority` | `sampled_latch_reset_priority` |
| `flash_adc_3b_smoke` | `FAIL_SIM_CORRECTNESS` | `quantizer_code_coverage` | `clocked_quantizer_code_coverage` |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `cadence_multimod_counts` | `counter_cadence_multimod_prescaler` |

## Eligible-4 H Repair After Checker Fix

Command:

```bash
python3 runners/signature_guided_h.py \
  --g-result-root results/runtime-profile-G-kimi-isolated-2026-04-26 \
  --anchor-root generated-table2-evas-guided-repair-3round-skill/kimi-k2.5 \
  --output-root results/signature-guided-H-Gfailed-eligible4-fixed-checker-2026-04-26 \
  --generated-root generated-signature-guided-H-Gfailed-eligible4-fixed-checker-2026-04-26 \
  --timeout-s 180 --workers 4 --resume \
  --tasks clk_divider dff_rst_smoke flash_adc_3b_smoke multimod_divider
```

Result:

| Metric | Value |
|---|---:|
| Tasks | 4 |
| Eligible | 4 |
| Best pass | 4 |
| Strict rescues over re-scored G | 3 |

Task-level result:

| Task | Re-scored G | H best | Best variant | Strict rescue |
|---|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `segment_ceil_low_floor_high` | Yes |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `pulse_every_base_or_base_plus_one_reset0` | Yes |
| `dff_rst_smoke` | `PASS` | `PASS` | `baseline` | No |
| `flash_adc_3b_smoke` | `FAIL_SIM_CORRECTNESS` | `PASS` | `clocked_uniform_3b_quantizer` | Yes |

Interpretation:

- The current strict H rescue evidence is `3/4` on eligible tasks, or `3`
  strict rescues among the 41 historical G-failed tasks after re-scoring.
- `dff_rst_smoke` should not be counted as an H rescue; it is a checker-window
  correction that turns the existing artifact/gold behavior into PASS.
- A separate formal end-to-end repair-artifact scorer is now needed to quantify
  how often repaired DUT behavior also transfers through generated testbenches.

## Why The Remaining H Cases Are Not Fixed

After latest re-score, the 41 historical G-failed tasks split as:

| Bucket | Count |
|---|---:|
| Re-scored G already PASS | 10 |
| Strict H rescue | 3 |
| Eligible but already PASS after checker fix | 1 |
| Still unresolved | 28 |

Representative unresolved cases:

| Case | Failure evidence | Reason H does not repair it yet |
|---|---|---|
| `pfd_deadzone_smoke` | `behavior_eval_timeout>26s` | H cannot safely trigger a PFD timing-window template without pulse/phase metrics. |
| `pfd_reset_race_smoke` | `evas_timeout>80s` | The harness is too slow or times out before useful behavior diagnostics are produced. |
| `dwa_ptr_gen_no_overlap_smoke` | onehot family detected, but `evas_timeout>80s` | Existing exploratory DWA template assumes scalar-expanded ports, while this anchor is bus-style; H correctly refuses an interface-breaking patch. |
| `adpll_ratio_hop_smoke` | `pre_ratio=8.000 post_ratio=8.000 pre_lock=0.000 post_lock=0.000` | Complex PLL system behavior requires submodule/local-loop decomposition, not a single generic template. |
| `cppll_tracking_smoke` | `freq_ratio=1.0889 fb_jitter_frac=0.0446 lock_time=nan` | Needs loop/timing-window reasoning and lock metrics; current H has no safe PLL template. |
| `cdac_cal` | `no vdac activity` | Needs a CDAC calibration/output-activity template and localization of code update vs DAC output path. |
| `multimod_divider_ratio_switch_smoke` | `not_enough_edges in=320 out=0` | Current multimod template handles wrong count values, not a completely missing output cadence. |
| `nrz_prbs` | `transitions=0 complement_err=0.0041 swing=0.900` | Needs a PRBS/LFSR sequence-state template; not yet promoted to formal H. |
| `digital_basics_smoke` | `tb_not_executed`, `tran.csv missing` | This is compile/harness closure, not DUT behavior repair. |
| `segmented_dac` | no parseable single-module anchor | Current H requires a single DUT module; multi-module H is future work. |

Takeaway:

- H succeeds when the failure is covered by a promoted mechanism family and the
  DUT interface matches that family.
- H intentionally refuses to act when evidence is timeout-only, compile-level,
  multi-module, or outside the current template registry. This is a feature,
  not just a limitation, because it avoids task-name overfitting.

## Formal H Materialization

Implementation:

- Added `runners/materialize_condition_h.py`.
- The script copies the base condition's selected best-round artifact into a
  normal `generated/`-style tree.
- For strict H rescues, it replaces only the DUT `.va` file.
- The generated testbench remains from the base condition, so this measures
  formal end-to-end transfer rather than gold-harness DUT correctness.

H-on-F result:

| Condition | Scoring config | Formal pass |
|---|---|---:|
| `F-stable` | `workers=4 timeout=160 save-policy=contract` | 58/92 |
| `H-on-F-stable` | `workers=4 timeout=160 save-policy=contract` | 59/92 |

Formal gain:

| Task | F-stable evidence | H-on-F evidence | Explanation |
|---|---|---|---|
| `multimod_divider` | `FAIL_SIM_CORRECTNESS`, `base=4 pre_count=4 post_count=4` | `PASS`, `base=4 pre_count=9 post_count=9` | H's multimod cadence template fixes the DUT while keeping the formal harness valid. |

Non-transfer example:

| Task | DUT-side H | Formal H-on-F | Reason |
|---|---|---|---|
| `flash_adc_3b_smoke` | PASS under gold/reference harness, `codes=8/8 reversals=0` | `FAIL_SIM_CORRECTNESS`, `too_few_edges=0` | The generated testbench does not exercise the ADC clock correctly, so a fixed DUT cannot be observed as formal PASS. |

Conclusion:

- H is now connected to formal scoring.
- Under the fair stable config, it improves the best Kimi formal result from
  `58/92` to `59/92`.
- The main remaining bottleneck is cross-artifact repair: some H DUT fixes need
  generated-testbench/harness repair before they can become end-to-end passes.
