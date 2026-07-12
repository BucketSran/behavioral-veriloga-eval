# VGA Gain Calibration Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `vga_cal_loop_top.va`, `peak_detector.va`, `gain_controller.va`, `vga_model.va`, `lock_detector.va`
- Public top module: `vga_cal_loop_top`
- Required public modules: `vga_cal_loop_top`, `peak_detector`, `gain_controller`, `vga_model`, `lock_detector`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `vga_cal_loop_top` with positional electrical ports `vin, target, clk, rst, start, vout, gain_3, gain_2, gain_1, gain_0, locked, peak_metric`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `peak_detector(vin, clk, rst, start, peak_metric)`; parameters: vth=0.45, tr=200e-12.
- `gain_controller(peak_metric, target, clk, rst, start, gain_3, gain_2, gain_1, gain_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tol=20e-3, tr=200e-12.
- `vga_model(vin, gain_3, gain_2, gain_1, gain_0, vout)`; parameters: vth=0.45, gain_min=0.5, gain_lsb=0.1.
- `lock_detector(peak_metric, target, clk, rst, start, locked)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tol=20e-3, tr=200e-12.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for `clk`, `rst`, and `start`.
- `gain_min = 0.5`: gain for code 0.
- `gain_lsb = 0.1`: gain increment per code step.
- `tol = 20e-3 V`: lock tolerance around the target peak.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, set gain code to 4, clear `locked`, clear `peak_metric`, and drive `vout` from the reset gain.
- When `start` is high, `peak_detector` samples the absolute magnitude of `vin` on each rising `clk` edge.
- `vga_model` drives `vout = (gain_min + gain_lsb * gain_code) * V(vin)`.
- `gain_controller` increments the gain code by one when `peak_metric` is below `V(target) - tol`, decrements it by one when above `V(target) + tol`, and otherwise holds it.
- Clamp the gain code to the range 0 to 15.
- `lock_detector` asserts `locked` after three consecutive update cycles where the peak is within tolerance.
- Drive `gain_3..gain_0` as voltage-coded copies of the current gain code.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `vga_cal_loop_top.va`
- `peak_detector.va`
- `gain_controller.va`
- `vga_model.va`
- `lock_detector.va`
