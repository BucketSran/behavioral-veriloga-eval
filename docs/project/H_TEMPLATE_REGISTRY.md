# H Template Registry

Condition H is defined as:

`G + signature-gated mechanism templates + EVAS candidate selection`

Current implementation scope: DUT-side repair using the benchmark
gold/reference testbench as the behavior harness. Full end-to-end
generated-testbench closure must be measured separately.

The template policy must not trigger from task id alone. A template is eligible
only when both conditions hold:

1. EVAS failure notes expose a supported failure signature.
2. The generated DUT/TB interface signature matches a reusable mechanism family.

## Promotion Rules

| Status | Meaning | Paper usage |
|---|---|---|
| `formal_candidate` | Rescues multiple tasks or one task family with reusable signature evidence. | Can be used in the formal H method after full validation. |
| `exploratory` | Rescues one task or has only limited evidence. | Keep for development; do not use as a core claim yet. |
| `disabled` | Caused regressions or has checker-equivalence risk. | Do not use in reported scoring. |

## Template Families

| Family | Failure signature | Interface signature | Current status | Notes |
|---|---|---|---|---|
| `counter_cadence/off-by-one` | `ratio_code`, `interval_hist`, `base/pre_count/post_count` | Clock input plus divider/control outputs | `formal_candidate` | Already rescued `clk_divider` and `multimod_divider` in supported H smoke tests. |
| `sampled_latch/reset_priority` | `q_mismatch`, `edge/sample mismatch`, reset priority mismatch | D/Q/QB/CLK/RST or sample/hold style ports | `exploratory` | Needs a reusable skeleton that preserves edge choice and reset polarity. |
| `quantizer/code_coverage` | `only_N_codes`, `codes=x/y`, `unique_codes`, monotonic/reversal notes | VIN/CLK/output bits or DAC input bits/AOUT | `formal_candidate` | 3-bit ADC code-coverage template rescued `flash_adc_3b_smoke`; broader DAC/ADC templates still exploratory. |
| `onehot/thermometer/no-overlap` | `overlap`, `ptr`, `cell_en`, thermometer/wrap notes | One-hot pointer/cell enable or thermometer buses | `exploratory` | Useful for DWA/thermometer families; must avoid task-specific bus widths where possible. |
| `frame/sequence_alignment` | `frame`, `sequence`, `PRBS`, `LFSR`, bit mismatch notes | CLK/load/frame/serial or seed/state sequence ports | `exploratory` | Needs generic load/capture/shift phase candidates. |
| `PFD/PLL timing_window` | `up_frac`, `dn_frac`, pulse count/width, lock/reacquire/frequency notes | REF/DIV/UP/DN or PLL lock/frequency observables | `exploratory` | High value but sensitive; checker windows must be preserved. |
| `multi-module interface sanity` | `tran.csv missing`, missing generated include, module/interface mismatch | Multiple includes/modules or generated TB/DUT boundary | `exploratory` | Should repair wiring/save/include issues before behavior templates. |

## Current Evidence

| Evidence set | Result |
|---|---|
| Supported H smoke | `clk_divider`, `multimod_divider`, `flash_adc_3b_smoke` all rescued from G-failed anchors. |
| Signature-gated H smoke | After the DFF checker-window fix, the eligible-4 run reached `4/4` best pass with `3` strict rescues over re-scored G. `dff_rst_smoke` is not counted as a rescue because the re-scored baseline now passes. See `H_SIGNATURE_GUIDED_SMOKE_2026-04-26.md`. |
| G runtime taxonomy | See `H_FAILURE_TAXONOMY_G_KIMI_2026-04-26.md`; many failures remain `unsupported/behavior_other`, so template coverage must expand carefully. |
| Speed profile | See `SLOW_TASK_REPORT_G_KIMI_2026-04-26.md`; H validation should use `--resume`, isolated outputs, and contract save policy. |

## Required Per-Template Log

Every new template family should record:

| Field | Required content |
|---|---|
| Trigger | EVAS note pattern and interface/module condition. |
| Candidate space | What bounded variants are generated. |
| Invariants | What files, ports, save names, stimulus, or checker contract must be preserved. |
| Evidence | Eligible tasks, rescued tasks, unsupported tasks, regressions. |
| Status decision | `formal_candidate`, `exploratory`, or `disabled`. |

## Non-Goals

- Do not use task id as the trigger.
- Do not copy gold implementation details.
- Do not report single-case exploratory templates as universal method evidence.
- Do not enable experimental streaming checkers in formal scoring unless parity
  is validated and recorded. Current proof is in
  `docs/project/STREAMING_CHECKER_PARITY_2026-04-26.md`; the validated subset is
  now promoted to the default scoring path.
