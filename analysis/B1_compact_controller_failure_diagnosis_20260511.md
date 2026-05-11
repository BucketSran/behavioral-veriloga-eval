# B1 Compact-Controller Failure Diagnosis - 2026-05-11

This note explains why the full 8-task compact-controller fallback run reached
official EVAS `3/8`, and why the remaining tasks did not pass.

Authoritative result root:
`results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511`

Admission table:
`analysis/B1_compact_controller_fallback_admission_20260511.md`

## What The 3 PASS Actually Mean

| Task | Source -> official | Mechanism role |
| --- | --- | --- |
| `vbm1_edge_detector_dut` | `PASS -> PASS` | Pre-existing pass preserved; no repair call. |
| `vbm1_vco_phase_integrator_dut` | `PASS -> PASS` | Pre-existing pass preserved; no repair call. |
| `vbm1_resettable_counter_divider_dut` | `FAIL_DUT_COMPILE -> PASS` | The only new pass from this run. Compact fallback triggered and generated `clk_divider_ref.va`. |

Therefore the current mechanism added one new official EVAS pass.  It did not
repair two additional behavior tasks; it preserved them.

## Why Fallback Only Added One Pass

The implemented fallback trigger uses compact-controller only for
compile/runtime/observable blockers.  In this run, only
`vbm1_resettable_counter_divider_dut` was classified as `compile_dut`, so only
that task used compact-controller:

- prompt chars: `5242`
- API elapsed: `105.407s`
- official notes: `ratio=5 in_edges=80 out_edges=16 ... lock=1`

All five remaining failures were classified as `behavior`, so they stayed on the
old full adaptive prompt path:

- prompt chars: `12294` to `15354`
- compact used: `False`
- result: no official EVAS improvement

This is the central finding: blocker-only fallback is useful, but too narrow.

## Remaining Failure Mechanisms

| Task | Official note | What failed | Diagnosis |
| --- | --- | --- | --- |
| `vbm1_background_calibration_accumulator_bugfix` | `first=0.003 mid=0.004 late=0.006` | Expected `first>0.52`, then mid lower, then late higher. | Candidate uses `vstep=0.001`, starts at zero, and only increments when `err>0.5`; it never decrements when `err=0`. The output is near zero and monotonic tiny-increase, not a signed/background calibration waveform. |
| `vbm1_cdac_calibration_dut` | `first=0.944 mid=0.943 late=0.944` | Expected meaningful down-then-up trim movement. | Candidate starts high at `0.94` and uses `step_size=0.001`; only a millivolt-scale change occurs. It has the right direction idea but step magnitude and target waveform are wrong. |
| `vbm1_first_order_lowpass_dut` | `ZeroDivisionError`, `tran.csv missing` | Simulation runtime artifact failure. | Candidate computes `tau = 1/(2*pi*fc)` as a parameter expression and divides by `tau` during each analog evaluation. EVAS runtime sees a zero denominator in the generated model path, so no waveform is produced. This needs a numerically safe analog dynamics template, not another long prompt. |
| `vbm1_barrel_pointer_window_bugfix` | `count_range=(0, 0)` | All `win0..win3` stay low. | Candidate preserved the buggy direction pattern: `win0`, `win1`, `win2` are inputs and only `win3` is output. The fixed harness does not drive `win0..win3`; the DUT must drive all four window outputs. |
| `vbm1_leaky_hold_dut` | `high=0.000 decayed=0.000 rst=0.000` | Output never rises. | Candidate samples `V(sample)` exactly at the rising crossing. Under EVAS event timing this sampled value is effectively zero, so held state remains zero. The repair needs a sample-event template that assigns a fixed high/held target on sample, then decays and resets. |

## Implication

The current compact-controller solves candidate completeness and simple
compile/interface blocker repair.  It does not solve behavior repair when the
task requires a mechanism-specific waveform shape.

The next strategy should not be "add back the whole skill bundle."  It should be
a two-trigger controller:

1. Use compact-controller for compile/runtime/observable blockers.
2. For behavior-layer tasks, route to compact mechanism templates:
   - calibration accumulator / CDAC: down-then-up bounded signed accumulator
   - first-order / leaky hold: numerically safe analog dynamics
   - barrel pointer: multi-output rotating adjacent window

Expected next target: move from official EVAS `3/8` to `5/8` by repairing the
barrel pointer and one of the calibration/analog dynamics tasks with compact
mechanism prompts.
