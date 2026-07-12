# Sigma-delta Modulator Mini Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `sigma_delta_top.va`, `integrator_state.va`, `sd_comparator.va`, `feedback_dac.va`, `decimator_lite.va`
- Public top module: `sigma_delta_top`
- Required public modules: `sigma_delta_top`, `integrator_state`, `sd_comparator`, `feedback_dac`, `decimator_lite`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `sigma_delta_top` with positional electrical ports `vin, clk, rst, bit_out, avg_3, avg_2, avg_1, avg_0, state_metric`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: midscale reference for the loop.
- `vth = 0.45 V`: threshold for `clk` and `rst`.
- `state_limit = 1.8 V`: absolute clamp for the integrator state.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the integrator state, bit output, decimator count, and `avg_3..avg_0`.
- On each rising `clk` edge, `feedback_dac` produces `vdd` when the previous output bit was high and `vss` otherwise.
- `integrator_state` updates `state = clamp(state + V(vin) - feedback + vcm, -state_limit, state_limit)`.
- `sd_comparator` drives the next `bit_out` high when the updated state is greater than or equal to `vcm`, otherwise low.
- `decimator_lite` counts the number of high bits in each 16-sample window and drives that count on `avg_3..avg_0` at the end of the window. Because the public result bus is four bits wide, a count of 16 must saturate to code 15 rather than wrap to zero.
- `state_metric` must expose the current integrator state as a voltage.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `sigma_delta_top.va`
- `integrator_state.va`
- `sd_comparator.va`
- `feedback_dac.va`
- `decimator_lite.va`
