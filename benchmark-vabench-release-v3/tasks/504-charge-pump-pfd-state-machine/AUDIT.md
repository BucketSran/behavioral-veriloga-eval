# Honest SOP Audit: Charge Pump PFD State Machine

## Scope

PLL clock-and-timing extension task. Pure voltage-domain behavioral DUT that
implements a classic three-state phase-frequency detector as an `@cross`-driven
integer state machine and integrates its output onto a bounded control voltage
through a sampled `@timer` update.

## Provenance

Recast from the Cadence example
`VerilogA/Vloga_M05_VlogaModelDesc/chargepump.va` (PFD + charge pump + RC loop
filter three-in-one). The original uses an `@cross`-driven integer `state`
machine plus a structural RC network (`capacitor`/`resistor` instances) and an
`I(out)` current contribution. This recast keeps the `@cross` tri-state detector
verbatim but replaces the structural RC and current-domain pump with a
voltage-domain sampled integrator (`vctrl_q += state_q * pump_rate * tstep`)
driven on a `@timer(0, tstep)` tick. The structural RC and the `I(...)` branch
contribution are dropped per the v3 PLL-category voltage-domain contract.

## Four Standards

- Useful scenario: demonstrates the `@cross`-edge analog state-machine idiom
  (tri-state PFD) plus an event-driven sampled integrator, a modeling technique
  not present as a combined form in any existing v3 task.
- Reasonable task: the public prompt fixes the port contract, parameters, and
  the exact state-machine / integration equations.
- Complete tests: hidden and visible testbenches drive `ref` and `fb` as
  same-frequency square waves with a fixed phase offset, so the detector takes a
  consistent sign and the control voltage ramps monotonically; five concrete
  negative variants are materialized.
- Fair evaluation: the checker inspects the late-window `vctrl` trend (it must
  move toward the rail implied by the ref/fb lead relation and stay within the
  clamp band) and the `metric` polarity (it must report the detector state).

## Checker Context

- Checker id: `v3_504_charge_pump_pfd_state_machine` (row-based, registered in
  `runners/simulate_evas.py`).
- Inspects the early vs late `vctrl` window and counts `metric` samples in each
  polarity band; does not re-run the detector state machine (the DUT is the
  source of truth for edge timing).

## Certification Status

Behavior-extension-candidate. Verified against **Spectre 21.1** (ground truth,
via the thu-sui bridge) and the EVAS Python engine: gold PASS on both; all five
negatives rejected on both. Note: this task relies on a Verilog-A support clock
(`ref_fb_clk.va`) rather than a Spectre `vsource type=square` stimulus, because
EVAS did not previously fire `@cross` on square-driven nodes (EVAS defect D1,
tracked separately in `Arcadia-1/EVAS#68`). Under Spectre both stimulus forms
work; the support-clock form is used so EVAS and Spectre agree.
