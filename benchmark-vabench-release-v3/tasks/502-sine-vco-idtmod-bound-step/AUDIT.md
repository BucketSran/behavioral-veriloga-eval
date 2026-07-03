# Honest SOP Audit: Sine VCO With Idtmod And Bound Step

## Scope

PLL clock-and-timing extension task. Pure voltage-domain behavioral DUT that
exercises a continuous-time sine VCO built from an `idtmod()` phase integrator
plus a `$bound_step()` points-per-cycle limit.

## Provenance

Recast from the Cadence example
`BehavModelVAMS_M08_Operation/.solutions/VCO1.va` (VCO1 sine oscillator). The
original uses an offset sine `vco_amp + vco_amp*sin(...)`; this recast drops the
DC offset so the output is a bipolar `vco_amp*sin(2*pi*phase_q)` ranging
`-vco_amp` to `+vco_amp`, and adds a voltage-coded wrapped-phase `metric`
observable for calibration. The checker, gold, and all negatives are bipolar
and consistent. The structural `I()`/RC form of the loop is not used here; this
is the oscillator-only model.
Dropped `I()`/device instantiations per the v3 PLL-category voltage-domain
contract (`must_not_include: I(, ddt(, idt(`).

## Four Standards

- Useful scenario: demonstrates the canonical SpectreRF-friendly "no hidden
  state" sine VCO idiom (`idtmod` + `$bound_step`), which is not present as a
  combined technique in any existing v3 task.
- Reasonable task: the public prompt fixes the port contract, parameters, and
  the exact phase/frequency/output equations.
- Complete tests: hidden and visible testbenches hold `vin` constant so the
  output is a pure sine; five concrete negative variants are materialized.
- Fair evaluation: the checker re-integrates the phase from `V(vin)` with the
  same trapezoidal rule the simulator uses for `idtmod`, then checks `out`
  follows `vco_amp*sin(2*pi*phase)` and `metric` follows `vco_amp*phase`.

## Checker Context

- Checker id: `v3_502_sine_vco_idtmod_bound_step` (row-based, registered in
  `runners/simulate_evas.py`).
- Reintegrates phase with the shared `_v3_integrated_mod_phase_values` helper
  (modulus 1.0) and compares the sine/phase observables over a windowed stride.
- Note: `$bound_step` is treated as a syntax/modeling contract (it is captured
  via the `must_include` guard). The EVAS Python engine does not derive its
  timestep from `$bound_step`, so this task does not claim the behavior checker
  fully proves the points-per-cycle effect; under Spectre the construct is
  honored natively. The behavioral negatives (flat output, zero metric, phase
  shift, gain-sign flip, amplitude halving) all diverge from the
  reintegrated-phase reference.

## Certification Status

Behavior-extension-candidate. Verified against **Spectre 21.1** (ground truth,
via the thu-sui bridge) and the EVAS Python engine: gold PASS on both; all five
negatives rejected on both. Spectre and EVAS agree.
