# Buck Converter Controller Macro

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `buck_ctrl_top.va`, `soft_start.va`, `error_comparator.va`, `pwm_modulator.va`, `power_good.va`
- Public top module: `buck_ctrl_top`
- Required public modules: `buck_ctrl_top`, `soft_start`, `error_comparator`, `pwm_modulator`, `power_good`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `buck_ctrl_top` with positional electrical ports `vfb, vref, clk, rst, enable, pwm, duty_metric, soft_ref, pgood`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `duty_min = 0.05`: minimum duty metric.
- `duty_max = 0.95`: maximum duty metric.
- `soft_step = 25e-3 V`: soft-start reference increment per clock.
- `pgood_tol = 25e-3 V`: power-good tolerance.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear `pwm`, `duty_metric`, `soft_ref`, and `pgood`.
- `soft_start` ramps `soft_ref` toward `vref` by at most `soft_step` per rising `clk` edge.
- `error_comparator` compares `vfb` against `soft_ref` and requests a larger duty metric when feedback is low.
- `pwm_modulator` updates a bounded duty metric once per rising `clk` edge and drives `pwm` from that metric.
- Clamp `duty_metric` between `duty_min` and `duty_max`.
- `power_good` asserts `pgood` after three consecutive cycles where `vfb` is within `pgood_tol` of `vref`.
- This DUT models the controller only; it must not instantiate an inductor, switch device, or current-domain power stage.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `buck_ctrl_top.va`
- `soft_start.va`
- `error_comparator.va`
- `pwm_modulator.va`
- `power_good.va`
