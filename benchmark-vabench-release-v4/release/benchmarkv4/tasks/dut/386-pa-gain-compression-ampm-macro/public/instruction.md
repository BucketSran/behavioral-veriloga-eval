# PA Gain-compression and AM/PM Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `pa_gain_compression_ampm_macro.va`
- Public top module: `pa_gain_compression_ampm_macro`
- Required public module: `pa_gain_compression_ampm_macro`

The submitted source must include the target artifact and public module listed above. Optional helper modules may be included only when they are part of the DUT source package.

## Public Verilog-A Interface

Declare top module `pa_gain_compression_ampm_macro` with positional electrical ports `vin, envelope, enable, rst, vout, gain_metric, phase_metric, compressed`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference.
- `small_gain = 3.0`: small-signal voltage gain.
- `comp_threshold = 0.2 V`: envelope deviation where compression begins.
- `vth = 0.45 V`: threshold for enable and reset.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `vout` to `vcm`, clear metrics, and clear `compressed`.
- When enabled, amplify `vin - vcm` with high small-signal gain at low envelope.
- As `envelope` exceeds the compression threshold, reduce the effective gain monotonically.
- Expose the active gain on `gain_metric` and a monotonic AM/PM proxy on `phase_metric`.
- Assert `compressed` when the effective gain is below the small-signal gain by the configured compression condition.
- Clamp `vout` inside `[vss, vdd]`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add stimulus harnesses, simulator control decks, external validation logic, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The implementation must satisfy the top-level observable contract across public parameter overrides.

## Output Contract

Return exactly these complete source artifacts:

- `pa_gain_compression_ampm_macro.va`
