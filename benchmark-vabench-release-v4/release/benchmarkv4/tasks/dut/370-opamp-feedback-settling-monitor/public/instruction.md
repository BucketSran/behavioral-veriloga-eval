# Op-amp Feedback Settling Monitor

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `opamp_feedback_settling.va`
- Public top module: `opamp_feedback_settling`
- Required public module: `opamp_feedback_settling`

The submitted source must include the target artifact and public module listed above. Optional helper modules may be included only when they are part of the DUT source package.

## Public Verilog-A Interface

Declare top module `opamp_feedback_settling` with positional electrical ports `vin, clk, rst, enable, gain_2, gain_1, gain_0, vout, error_metric, settled`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: upper output clamp.
- `vss = 0.0 V`: lower output clamp.
- `vcm = 0.45 V`: common-mode reference.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `gain_lsb = 0.5`: closed-loop gain increment per gain-code step.
- `alpha = 0.3`: sampled settling factor.
- `settle_tol = 40e-3 V`: error tolerance for settled flag.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, drive `vout` to `vcm`, clear `error_metric`, and clear `settled`.
- Decode `gain_2..gain_0` into a closed-loop target gain of at least unity.
- Update `vout` once per rising `clk` edge toward the target closed-loop output using `alpha`.
- Clamp `vout` to the range `vss` through `vdd`.
- `error_metric` must expose the signed difference between the current output and the target closed-loop value.
- Assert `settled` after three consecutive updates where the absolute error is below `settle_tol`.
- The output must move in the direction of the target after an input step unless already clamped.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add stimulus harnesses, simulator control decks, external validation logic, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The implementation must satisfy the top-level observable contract across public parameter overrides.

## Output Contract

Return exactly these complete source artifacts:

- `opamp_feedback_settling.va`
