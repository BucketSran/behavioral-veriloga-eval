# Resistor Ladder Monotonic Decoder

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `resistor_ladder_monotonic_decoder.va`
- Public top module: `resistor_ladder_monotonic_decoder`
- Required public module: `resistor_ladder_monotonic_decoder`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `resistor_ladder_monotonic_decoder` with positional electrical ports `code_2, code_1, code_0, enable, rst, vout, step_metric, monotonic_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `vout` low, clear `step_metric`, and clear `monotonic_ok`.
- Decode `code_2..code_0` as an unsigned ladder tap index from 0 to 7.
- Drive `vout` to the corresponding evenly spaced ladder voltage between `vss` and `vdd`.
- Expose one LSB step on `step_metric` while enabled.
- Assert `monotonic_ok` when the active code-to-output mapping is nondecreasing.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `resistor_ladder_monotonic_decoder.va`
