# AM Modulator Source Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `am_modulator_source_macro.va`
- Public top module: `am_modulator_source_macro`
- Required public module: `am_modulator_source_macro`

The submitted source must include the target artifact and public module listed above. Optional helper modules may be included only when they are part of the DUT source package.

## Public Verilog-A Interface

Declare top module `am_modulator_source_macro` with positional electrical ports `carrier_in, mod_in, enable, rst, vout, envelope_dbg, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference.
- `mod_index = 0.5`: amplitude modulation sensitivity.
- `vth = 0.45 V`: threshold for `enable` and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `vout` to `vcm`, clear `envelope_dbg`, and clear `valid`.
- When enabled, treat `carrier_in` and `mod_in` as deviations around `vcm`.
- Drive an amplitude-modulated output whose carrier deviation increases when `mod_in` rises above `vcm` and decreases when it falls below `vcm`.
- Clamp the envelope multiplier so the output stays within `[vss, vdd]`.
- `envelope_dbg` must expose the active voltage-domain envelope multiplier mapped into the output voltage range.
- Assert `valid` while enabled after reset has been released.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add stimulus harnesses, simulator control decks, external validation logic, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The implementation must satisfy the top-level observable contract across public parameter overrides.

## Output Contract

Return exactly these complete source artifacts:

- `am_modulator_source_macro.va`
