# Common-mode Feedback Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `cmfb_loop_top.va`, `cm_sensor.va`, `trim_controller.va`, `output_balancer.va`
- Public top module: `cmfb_loop_top`
- Required public modules: `cmfb_loop_top`, `cm_sensor`, `trim_controller`, `output_balancer`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `cmfb_loop_top` with positional electrical ports `vop_in, von_in, clk, rst, enable, vop_out, von_out, trim_2, trim_1, trim_0, cm_error, locked`. All top-level ports are electrical.

Each required public helper module must be declared in the correspondingly named artifact with these positional electrical interfaces:

- `cm_sensor(vop_in, von_in, cm_error_raw)`
- `trim_controller(clk, rst, enable, cm_error_raw, trim_2, trim_1, trim_0, trim_corr, locked)`
- `output_balancer(vop_in, von_in, enable, rst, trim_corr, vop_out, von_out, cm_error)`

The top module and helper modules must expose exactly these public port orders.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: target common-mode voltage.
- `vth = 0.45 V`: threshold for clock, reset, and enable.
- `trim_lsb = 10e-3 V`: output correction represented by one trim step.
- `lock_tol = 10e-3 V`: common-mode error tolerance for lock.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear the trim code, drive outputs toward inputs without correction, clear `cm_error`, and clear `locked`.
- `cm_sensor` must measure the average of `vop_in` and `von_in` relative to `vcm`.
- `trim_controller` must update the unsigned trim code once per rising `clk` edge in the direction that reduces representable positive common-mode error, saturating at code 0 or 7.
- `output_balancer` must apply the trim correction symmetrically to `vop_out` and `von_out` without changing differential polarity.
- `trim_2..trim_0` must expose the active trim code and `cm_error` must expose the signed residual error.
- Assert `locked` after two consecutive updates within `lock_tol`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `cmfb_loop_top.va`
- `cm_sensor.va`
- `trim_controller.va`
- `output_balancer.va`
