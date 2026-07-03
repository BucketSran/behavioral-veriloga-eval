# Honest SOP Audit: Differential VCO With Clip And Idtmod

## Scope

PLL clock-and-timing extension task. Pure voltage-domain behavioral DUT that
exercises a fully-differential sine VCO built from an `idtmod()` phase
integrator, a file-scope `clip` macro for frequency clamping, and symmetric
differential outputs.

## Provenance

Recast from the Cadence example
`BehavModelVAMS_M08_Operation/.solutions/VCO_ams.vams` (differential AMS VCO).
The original uses `\`define clip` plus `idtmod` plus a differential contribution
`V(OUTP,OUTM)`. This recast splits the differential output into two single-ended
arms (`outp = Vcm + Vac*sin`, `outm = Vcm - Vac*sin`) so each arm is an
independent voltage-coded observable, and adds a wrapped-phase `metric`. The
current-domain form is not used. Voltage contributions only.

## Four Standards

- Useful scenario: demonstrates the differential-control + clip-macro + idtmod
  VCO idiom, which is not present as a combined technique in any existing v3
  task.
- Reasonable task: the public prompt fixes the port contract, the clip macro,
  the parameters, and the exact frequency/phase/output equations.
- Complete tests: hidden and visible testbenches hold the differential input
  constant so the output is a pure differential sine; five concrete negative
  variants are materialized.
- Fair evaluation: the checker re-integrates the phase from the differential
  input `V(vinp,vinm)` and checks that `outp` follows `Vcm+Vac*sin(2*pi*phase)`,
  `outm` follows `Vcm-Vac*sin(2*pi*phase)`, and `metric` follows `0.9*phase`.

## Checker Context

- Checker id: `v3_503_differential_vco_clip_idtmod` (row-based, registered in
  `runners/simulate_evas.py`).
- Reintegrates phase with the shared `_v3_integrated_mod_phase_values` helper
  (modulus 1.0) and compares all three observables over a windowed stride.
- The frequency clamp (`Fmin`/`Fmax`) is exercised by the hidden testbench only
  when the differential input would push the raw frequency out of band; for the
  chosen hidden stimulus (36 MHz) the clamp is inactive, so the clamp itself is
  enforced structurally via the `must_include: clip(` guard rather than by a
  dedicated behavioral negative.

## Certification Status

Syntax-extension-candidate. EVAS behavior check is the reference for this
branch; Spectre parity is `needs_rerun`.
