# Programmable Clock Skew Aligner

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `programmable_clock_skew_aligner.va`
- Public top module: `programmable_clock_skew_aligner`
- Required public module: `programmable_clock_skew_aligner`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `programmable_clock_skew_aligner` with positional electrical ports `clk_in, rst, enable, skew_2, skew_1, skew_0, clk_out, delay_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `unit_delay_metric = 0.1 V`: voltage-coded metric step per delay code.

## Required Behavior

- On reset or when disabled, drive output and metrics low.
- Decode `skew_2..skew_0` as a programmable output-edge delay code.
- For each accepted input clock edge, schedule one output edge after the code-dependent delay.
- Expose the active delay code as `delay_metric`.
- Assert `valid` after the first delayed output edge has been generated.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `programmable_clock_skew_aligner.va`
