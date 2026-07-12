# Offset-cancellation Servo

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `offset_servo_top.va`, `offset_sampler.va`, `trim_dac.va`, `error_integrator.va`
- Public top module: `offset_servo_top`
- Required public modules: `offset_servo_top`, `offset_sampler`, `trim_dac`, `error_integrator`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `offset_servo_top` with positional electrical ports `vinp, vinn, clk, rst, cal_en, corrected_out, trim_4, trim_3, trim_2, trim_1, trim_0, error_metric, done`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `trim_lsb = 2e-3 V`: offset correction per trim-code step.
- `error_tol = 5e-3 V`: residual offset tolerance.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the trim code, `corrected_out`, `error_metric`, and `done`.
- While `cal_en` is high, `offset_sampler` samples the differential input error once per rising `clk` edge.
- `error_integrator` updates a 5-bit trim code in the direction that reduces the sampled differential error.
- `trim_dac` converts the trim code to a signed correction applied to the differential input.
- `corrected_out` must expose the corrected differential signal as a voltage metric.
- Drive `trim_4..trim_0` as voltage-coded copies of the trim code.
- Assert `done` after four consecutive calibration updates where `error_metric` magnitude is within `error_tol`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `offset_servo_top.va`
- `offset_sampler.va`
- `trim_dac.va`
- `error_integrator.va`
