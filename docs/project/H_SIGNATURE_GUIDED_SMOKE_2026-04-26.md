# H Signature-Guided Smoke Result

Date: 2026-04-26

## Purpose

This smoke test checks the current condition-H direction:

`G artifact -> EVAS rescore -> failure signature -> module/interface gate -> bounded template candidates -> EVAS fitness selection`

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

