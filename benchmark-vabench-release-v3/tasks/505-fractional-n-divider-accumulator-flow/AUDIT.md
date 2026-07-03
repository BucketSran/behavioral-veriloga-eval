# Honest SOP Audit: Fractional-N Divider Accumulator Flow

## Scope

PLL clock-and-timing **system** flow (L2). Closes the v1 gap task
`vbr11_l2_fractional_n_pll_divider_flow`, which was proposed and marked
"certified" in `benchmark-vabench-release-v1/MANIFEST.json` but never
materialized on disk. The DUT is a fractional-N PLL: a behavioral DCO, an
integer feedback divider whose effective ratio is dithered by a modulo
accumulator (swallow-one-pulse on overflow), a PFD with proportional + bounded
integral correction, and a lock detector.

## Provenance

Modeled after the verified task `097-cppll-tracking-reacquire-timer`
(`cppll_timer_ref.va`), extended with the fractional accumulator dither. The
support clock `ref_step_clk.va` is a verbatim copy of the 097 support clock
idiom. Pure voltage-domain behavioral Verilog-A throughout: voltage
contributions only, no `I(...)`/`ddt(...)`/`idt(...)`.

## Four Standards

- Useful scenario: fractional-N division with accumulator dither is the
  canonical fractional-synthesizer primitive and was a documented gap in v1.
- Reasonable task: the public prompt fixes the port contract, parameters, and
  the divider/accumulator/loop equations.
- Complete tests: the hidden testbench steps the reference period
  (`period_pre` -> `period_post` at `t_switch`) so the loop must track and
  reacquire; five concrete negative variants are materialized.
- Fair evaluation: the checker compares the late-window feedback cadence to the
  new reference, requires `vctrl_mon` to move and stay inside the rails, and
  requires `lock` to drop and reassert around the disturbance.

## Checker Context

- Checker id: `v3_505_fractional_n_divider_accumulator_flow` (row-based,
  registered in `runners/simulate_evas.py`).
- The checker structure mirrors the 097 CPPLL checker: edge-count and ratio
  checks over early vs late windows, `vctrl_mon` bounding, and `lock` drop/reassert
  detection around `t_switch`.

## Certification Status

Behavior-extension-candidate. Verified against **Spectre 21.1** (ground truth,
via the thu-sui bridge) and the EVAS Python engine: gold PASS on both; all five
negatives rejected on both. The checker measures the late-window average
DCO-to-fb divide ratio against the documented effective average
`div_int - frac_word/acc_modulus` (hidden deck: 7.625), so `neg_005_wrong_fraction_word`
(overrides the dither to ratio 7.25) fails behaviorally rather than only via the
indirect lock/ratio checks. A `frac_word < acc_modulus` guard in the gold clamps
illegal overrides so the documented average-ratio formula stays well-defined.
Spectre and EVAS agree.
