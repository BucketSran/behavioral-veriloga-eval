# Benchmark Expansion Report

## Contributor

name: liangyuxuan  
date: 2026-05-27

## Summary

- seed_92 perturbation tasks: 6
- external architecture tasks: 2
- EVAS PASS: 8
- Spectre PASS: 0 (not run in this local onboarding round)

## Tasks

| task_id | source_type | source_seed/url | perturbation_axes | EVAS | Spectre | notes |
|---|---|---|---|---|---|---|
| v2_dac_binary_clk_5b_cadence_held_level | seed_92_perturbation | dac_binary_clk_4b_smoke | rename, parameter, negative_constraint | PASS | N/A | 5-bit renamed DAC, checker PASS |
| v2_dac_binary_clk_6b_refclk_recon_level | seed_92_perturbation | dac_binary_clk_4b_smoke | rename, parameter, negative_constraint | PASS | N/A | 6-bit DAC variant, checker PASS |
| v2_dac_binary_clk_3b_code_event_level | seed_92_perturbation | dac_binary_clk_4b_smoke | rename, parameter, negative_constraint | PASS | N/A | 3-bit DAC variant, checker PASS |
| v2_adc_dac_ideal_4b_renamed_recon | seed_92_perturbation | adc_dac_ideal_4b_smoke | rename, keyword_removal | PASS | N/A | ADC+DAC renamed interface |
| v2_adc_dac_ideal_4b_param_shift | seed_92_perturbation | adc_dac_ideal_4b_smoke | parameter, timing | PASS | N/A | vdd/input range shifted to 1.0V |
| v2_adc_dac_ideal_4b_negconstraint_strict | seed_92_perturbation | adc_dac_ideal_4b_smoke | negative_constraint, keyword_removal | PASS | N/A | stricter banned-pattern variant |
| v2_ext_hysteresis_cmp_window | external_architecture | https://openvaf.github.io/docs/getting-started/examples | external_architecture, stateful_threshold | PASS | N/A | external mechanism task 1 |
| v2_ext_hysteresis_cmp_window_offset | external_architecture | https://openvaf.github.io/docs/getting-started/examples | external_architecture, rename, parameter | PASS | N/A | external mechanism task 2 |

## Lessons

1. For EVAS stability, splitting multi-module DUTs into separate `.va` files avoids parser/module-discovery edge cases in task-local flows.
2. Checker sampling windows should be aligned to settled post-event regions; this reduces false negatives from transition overlap.
3. Perturbation tasks are faster to scale when a validated seed template is reused, then mutated along one or two explicit axes each.

## Promotion Recommendation

- promote now: EVAS-verified subset above (pending Spectre parity and human review)
- needs repair: none in current EVAS run set
- reject: none
