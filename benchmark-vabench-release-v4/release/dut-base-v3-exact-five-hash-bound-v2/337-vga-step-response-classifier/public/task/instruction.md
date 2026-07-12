# VGA Step-response Classifier

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `vga_step_response_classifier.va`
- Public top module: `vga_step_response_classifier`
- Required public module: `vga_step_response_classifier`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `vga_step_response_classifier` with positional electrical ports `vin, clk, rst, enable, gain_2, gain_1, gain_0, vout, overshoot_metric, settled`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `gain_lsb = 0.5`: gain increment per code.
- `settle_tol = 12e-3 V`: settled threshold.

## Required Behavior

- On reset or when disabled, drive `vout` to `vcm`, clear metric, and clear `settled`.
- On each enabled rising `clk` edge, decode the gain code and update the target output from `vin`.
- Apply bounded settling with a code-dependent overshoot proxy after large gain changes.
- Expose overshoot magnitude on `overshoot_metric`.
- Assert `settled` after two consecutive updates within `settle_tol` of the target.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `vga_step_response_classifier.va`
