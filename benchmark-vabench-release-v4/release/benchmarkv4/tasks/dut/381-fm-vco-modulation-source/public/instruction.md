# FM/VCO Modulation Source Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `fm_vco_modulation_source.va`
- Public top module: `fm_vco_modulation_source`
- Required public module: `fm_vco_modulation_source`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `fm_vco_modulation_source` with positional electrical ports `mod_in, enable, rst, osc_out, freq_metric, phase_marker, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: modulation center voltage.
- `f0 = 10e6 Hz`: nominal oscillation frequency.
- `kvco = 5e6 Hz/V`: frequency sensitivity around `vcm`.
- `vth = 0.45 V`: threshold for `enable` and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `osc_out`, `freq_metric`, `phase_marker`, and `valid` low.
- When enabled, generate a deterministic behavioral oscillator whose frequency increases monotonically with `mod_in`.
- Clamp the commanded frequency to a nonnegative range and expose the normalized command on `freq_metric`.
- `osc_out` must toggle between `vss` and `vdd` according to the commanded oscillator state.
- `phase_marker` must pulse or toggle once per oscillator cycle so cycle period order is observable from public behavior.
- Assert `valid` after the first completed oscillator cycle following enable.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `fm_vco_modulation_source.va`
