# Buck Soft-start Ramp Controller

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `buck_soft_start_ramp_controller.va`
- Public top module: `buck_soft_start_ramp_controller`
- Required public module: `buck_soft_start_ramp_controller`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `buck_soft_start_ramp_controller` with positional electrical ports `clk, rst, enable, target_ref, soft_ref, ramp_metric, done`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `ramp_step = 40e-3 V`: soft-start increment.
- `ramp_tol = 5e-3 V`: done threshold.

## Required Behavior

- On reset or when disabled, clear `soft_ref`, ramp metric, and `done`.
- On each enabled rising `clk` edge, increase `soft_ref` toward `target_ref` by at most `ramp_step`.
- Never allow `soft_ref` to exceed `target_ref` or the public rails.
- Expose the remaining ramp distance on `ramp_metric`.
- Assert `done` only after `soft_ref` reaches the target within `ramp_tol`.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `buck_soft_start_ramp_controller.va`
