# Two-stage Op-amp Slew Macromodel

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `two_stage_opamp_slew_macromodel.va`
- Public top module: `two_stage_opamp_slew_macromodel`
- Required public module: `two_stage_opamp_slew_macromodel`

The submitted source must include the target artifact and public module listed above. Optional helper modules may be included only when they are part of the DUT source package.

## Public Verilog-A Interface

Declare top module `two_stage_opamp_slew_macromodel` with positional electrical ports `vinp, vinn, clk, rst, enable, load_step, vout, stage1_metric, slew_metric, clamp_flag, settled`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `stage1_gain = 20.0`: first-stage differential gain metric.
- `stage2_gain = 5.0`: second-stage gain from first-stage metric to output target.
- `slew_step = 80e-3 V`: maximum output movement per enabled clock edge.
- `settle_tol = 10e-3 V`: output error tolerance for `settled`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, drive `vout` and `stage1_metric` to `vcm`, clear `slew_metric`, `clamp_flag`, and `settled`.
- On each rising `clk` edge while enabled, sample the differential input `vinp - vinn`.
- Compute a first-stage metric from the sampled differential input, centered around `vcm` and limited to `[vss, vdd]`.
- Compute an output target from the first-stage metric and `stage2_gain`; `load_step` may request a bounded target perturbation around the same common-mode reference.
- Clamp the output target to `[vss, vdd]` and assert `clamp_flag` only when clamping occurs.
- Move `vout` toward the clamped target by no more than `slew_step` per enabled clock edge.
- `slew_metric` must expose the magnitude of the most recent output movement.
- Assert `settled` only after the output error has remained within `settle_tol` for two consecutive enabled updates.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add stimulus harnesses, simulator control decks, external validation logic, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The implementation must satisfy the top-level observable contract across public parameter overrides.

## Output Contract

Return exactly these complete source artifacts:

- `two_stage_opamp_slew_macromodel.va`
