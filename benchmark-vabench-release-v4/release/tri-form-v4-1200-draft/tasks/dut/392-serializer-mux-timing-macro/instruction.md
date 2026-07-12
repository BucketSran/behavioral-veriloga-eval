# Serializer MUX Timing Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `serializer_mux_timing_macro.va`
- Public top module: `serializer_mux_timing_macro`
- Required public module: `serializer_mux_timing_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `serializer_mux_timing_macro` with positional electrical ports `clk, rst, enable, d0, d1, d2, d3, serial_out, slot_1, slot_0, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for digital-voltage inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear `serial_out`, slot outputs, and `valid`.
- When enabled, step through inputs `d0`, `d1`, `d2`, and `d3` on successive rising `clk` edges.
- Drive `serial_out` as the voltage-coded value of the active input slot.
- `slot_1..slot_0` must expose the active slot index.
- Assert `valid` after the first complete four-slot frame.
- This is a serializer timing DUT, not a generic bus splitter.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `serializer_mux_timing_macro.va`
