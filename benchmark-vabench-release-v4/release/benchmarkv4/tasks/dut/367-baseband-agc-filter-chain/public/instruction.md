# Baseband AGC and Filter Chain

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `agc_chain_top.va`, `level_meter.va`, `gain_controller.va`, `vga_stage.va`, `filter_stage.va`
- Public top module: `agc_chain_top`
- Required public modules: `agc_chain_top`, `level_meter`, `gain_controller`, `vga_stage`, `filter_stage`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `agc_chain_top` with positional electrical ports `vin, target, clk, rst, enable, vout, gain_3, gain_2, gain_1, gain_0, level_metric, clip_flag, settled`. All top-level ports are electrical.

Each required public helper module must be declared with these positional electrical ports:

- `level_meter(vin, clk, rst, enable, level_metric)`
- `gain_controller(level_metric, target, clk, rst, enable, gain_3, gain_2, gain_1, gain_0, settled)`
- `vga_stage(vin, rst, enable, gain_3, gain_2, gain_1, gain_0, vga_out)`
- `filter_stage(vga_in, clk, rst, enable, vout, clip_flag)`

The top module must expose exactly the public top-level port order above and connect the required helper modules as part of the DUT package.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `gain_min = 0.5`: gain for code 0.
- `gain_lsb = 0.1`: gain increment per code step.
- `alpha = 0.25`: sampled low-pass smoothing factor.
- `tol = 20e-3 V`: target-level tolerance.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, set gain code to 4, clear metrics, clear flags, and drive `vout` to `vcm`.
- `level_meter` measures the magnitude of `vin` deviation from `vcm` once per rising `clk` edge.
- `gain_controller` increments the gain code when the measured level is below `V(target) - tol` and decrements it when above `V(target) + tol`.
- `vga_stage` applies the selected gain to the input deviation from `vcm`.
- `filter_stage` applies sampled low-pass smoothing to the VGA output.
- `clip_flag` must assert when the unclamped filtered output would exceed `vss` through `vdd`.
- `settled` must assert after three consecutive updates where `level_metric` is within tolerance.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `agc_chain_top.va`
- `level_meter.va`
- `gain_controller.va`
- `vga_stage.va`
- `filter_stage.va`
