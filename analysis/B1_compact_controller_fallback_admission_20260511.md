# B1 Compact-Controller Fallback Admission - 2026-05-11

Authoritative validator: `runners/validate_benchmark_v2_gold.py --backend evas`.

## Result

- Official EVAS: `3/8`
- Pass tasks: `vbm1_edge_detector_dut, vbm1_resettable_counter_divider_dut, vbm1_vco_phase_integrator_dut`
- Generated root: `generated-b1-compact-controller-fallback-dut-mimo-mt32768-20260511`
- Official result root: `results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511`
- Adaptive result root: `results/b1-compact-controller-fallback-dut-mimo-mt32768-adaptive-20260511`

## Admission Table

| Task | Source -> official | Repair layer | Compact used | Prompt chars | API s | Finish | Saved | Notes |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `vbm1_background_calibration_accumulator_bugfix` | `FAIL_SIM_CORRECTNESS->FAIL_SIM_CORRECTNESS` | `behavior` | `False` | 13699 | 81.370 | `stop` | 1 | contract_save_pruned=removed:1,inserted:1,signals:4; spectre_strict:preflight_pass |
| `vbm1_cdac_calibration_dut` | `FAIL_SIM_CORRECTNESS->FAIL_SIM_CORRECTNESS` | `behavior` | `False` | 15354 | 88.956 | `stop` | 1 | contract_save_pruned=removed:1,inserted:1,signals:4; spectre_strict:preflight_pass |
| `vbm1_first_order_lowpass_dut` | `FAIL_SIM_CORRECTNESS->FAIL_SIM_CORRECTNESS` | `behavior` | `False` | 12294 | 47.327 | `stop` | 1 | contract_save_pruned=removed:1,inserted:1,signals:2; spectre_strict:preflight_pass |
| `vbm1_vco_phase_integrator_dut` | `PASS->PASS` | `done` | `n/a` | n/a | n/a | `n/a` | 0 | contract_save_pruned=removed:1,inserted:1,signals:3; spectre_strict:preflight_pass |
| `vbm1_edge_detector_dut` | `PASS->PASS` | `done` | `n/a` | n/a | n/a | `n/a` | 0 | contract_save_pruned=removed:1,inserted:1,signals:3; spectre_strict:preflight_pass |
| `vbm1_resettable_counter_divider_dut` | `FAIL_DUT_COMPILE->PASS` | `compile_dut` | `True` | 5242 | 105.407 | `stop` | 1 | contract_save_pruned=removed:3,inserted:1,signals:12; spectre_strict:preflight_pass |
| `vbm1_barrel_pointer_window_bugfix` | `FAIL_SIM_CORRECTNESS->FAIL_SIM_CORRECTNESS` | `behavior` | `False` | 12425 | 44.627 | `stop` | 1 | contract_save_pruned=removed:1,inserted:1,signals:6; spectre_strict:preflight_pass |
| `vbm1_leaky_hold_dut` | `FAIL_SIM_CORRECTNESS->FAIL_SIM_CORRECTNESS` | `behavior` | `False` | 12609 | 83.666 | `stop` | 1 | contract_save_pruned=removed:1,inserted:1,signals:3; spectre_strict:preflight_pass |

## Findings

- Compact-controller fallback achieved the conservative target: official EVAS improved from `2/8` to `3/8` by adding `vbm1_resettable_counter_divider_dut` while preserving the two prior passes.
- Only `vbm1_resettable_counter_divider_dut` used compact-controller in this fallback run. The pure behavior-layer tasks stayed on the full prompt path and did not improve.
- `vbm1_first_order_lowpass_dut` regressed to a runtime-interface failure after repair. This shows the fallback trigger is too narrow for analog dynamics tasks whose base result is classified as behavior but whose repairs often create runtime artifacts.
- Provider latency remains nontrivial even with compact prompts; use wall-time control or smaller step prompts in the next loop.

## Next Strategy Update

Use a two-trigger controller instead of current fallback-only routing:

1. Always use compact-controller for compile/runtime/observable blockers.
2. Also use compact mechanism prompts for known high-risk behavior families: first-order/leaky analog dynamics, divider/counter state machines, and calibration accumulators.
3. Add task-family mechanism templates only after the compact controller has selected the failure family; do not restore the large skill bundle.
