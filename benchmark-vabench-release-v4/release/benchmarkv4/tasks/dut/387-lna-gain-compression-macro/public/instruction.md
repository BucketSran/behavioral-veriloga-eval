# LNA Gain-compression Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `lna_gain_compression_macro.va`
- Public top module: `lna_gain_compression_macro`
- Required public module: `lna_gain_compression_macro`

The submitted source must include the target artifact and public module listed above. Optional helper modules may be included only when they are part of the DUT source package.

## Public Verilog-A Interface

Declare top module `lna_gain_compression_macro` with positional electrical ports `vin, enable, rst, vout, gain_metric, compression_flag`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference.
- `small_gain = 4.0`: small-signal voltage gain.
- `input_clip = 0.18 V`: input deviation where gain compression starts.
- `vth = 0.45 V`: threshold for enable and reset.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `vout` to `vcm`, clear `gain_metric`, and clear `compression_flag`.
- When enabled, provide high gain for small input deviations around `vcm`.
- Reduce effective gain monotonically when the absolute input deviation exceeds `input_clip`.
- Expose active gain on `gain_metric` and assert `compression_flag` during compressed operation.
- Clamp `vout` inside `[vss, vdd]`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add stimulus harnesses, simulator control decks, external validation logic, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The implementation must satisfy the top-level observable contract across public parameter overrides.

## Output Contract

Return exactly these complete source artifacts:

- `lna_gain_compression_macro.va`
