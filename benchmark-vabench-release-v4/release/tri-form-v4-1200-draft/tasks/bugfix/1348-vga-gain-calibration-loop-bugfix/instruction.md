# VGA Gain Calibration Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `vga_cal_loop_top.va`:
  - Module `vga_cal_loop_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `target` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `start` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `gain_3` (output, electrical)
    - position 7: `gain_2` (output, electrical)
    - position 8: `gain_1` (output, electrical)
    - position 9: `gain_0` (output, electrical)
    - position 10: `locked` (output, electrical)
    - position 11: `peak_metric` (output, electrical)
- Artifact `peak_detector.va`:
  - Module `peak_detector` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `start` (input, electrical)
    - position 4: `peak_metric` (output, electrical)
- Artifact `gain_controller.va`:
  - Module `gain_controller` (required_submodule)
    - position 0: `peak_metric` (input, electrical)
    - position 1: `target` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `start` (input, electrical)
    - position 5: `gain_3` (output, electrical)
    - position 6: `gain_2` (output, electrical)
    - position 7: `gain_1` (output, electrical)
    - position 8: `gain_0` (output, electrical)
- Artifact `vga_model.va`:
  - Module `vga_model` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `gain_3` (input, electrical)
    - position 2: `gain_2` (input, electrical)
    - position 3: `gain_1` (input, electrical)
    - position 4: `gain_0` (input, electrical)
    - position 5: `vout` (output, electrical)
- Artifact `lock_detector.va`:
  - Module `lock_detector` (required_submodule)
    - position 0: `peak_metric` (input, electrical)
    - position 1: `target` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `start` (input, electrical)
    - position 5: `locked` (output, electrical)

## Public Parameter Contract

- `vga_cal_loop_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `vga_cal_loop_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `vga_cal_loop_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `vga_cal_loop_top.gain_min` defaults to `0.5`; valid range: finite; overrides gain_min for this module.
- `vga_cal_loop_top.gain_lsb` defaults to `0.1`; valid range: finite; overrides gain_lsb for this module.
- `vga_cal_loop_top.tol` defaults to `20e-3` V; valid range: finite and consistent with the declared rail domain; overrides tol for this module.
- `vga_cal_loop_top.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `peak_detector.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `peak_detector.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `gain_controller.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `gain_controller.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `gain_controller.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `gain_controller.tol` defaults to `20e-3` V; valid range: finite and consistent with the declared rail domain; overrides tol for this module.
- `gain_controller.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `vga_model.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `vga_model.gain_min` defaults to `0.5`; valid range: finite; overrides gain_min for this module.
- `vga_model.gain_lsb` defaults to `0.1`; valid range: finite; overrides gain_lsb for this module.
- `lock_detector.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `lock_detector.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `lock_detector.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `lock_detector.tol` defaults to `20e-3` V; valid range: finite and consistent with the declared rail domain; overrides tol for this module.
- `lock_detector.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_VGA_RESET_STATE`: restore: Reset restores gain code four and clears peak_metric and locked. Required traces: `time`, `clk`, `rst`, `gain_3`, `gain_2`, `gain_1`, `gain_0`, `peak_metric`, `locked`.
- `P_VGA_PEAK_SAMPLE`: restore: Each enabled rising clock samples the absolute vin magnitude into peak_metric. Required traces: `time`, `vin`, `clk`, `rst`, `start`, `peak_metric`.
- `P_VGA_GAIN_DIRECTION`: restore: The gain code moves one bounded step toward target according to the prior sampled peak and clamps to zero through fifteen. Required traces: `time`, `target`, `clk`, `rst`, `start`, `peak_metric`, `gain_3`, `gain_2`, `gain_1`, `gain_0`.
- `P_VGA_OUTPUT_GAIN`: restore: vout continuously equals vin times gain_min plus gain_lsb times gain code. Required traces: `time`, `vin`, `vout`, `gain_3`, `gain_2`, `gain_1`, `gain_0`.
- `P_VGA_LOCK_QUALIFICATION`: restore: locked asserts after three consecutive enabled updates whose prior sampled peak lies within tolerance. Required traces: `time`, `target`, `clk`, `rst`, `start`, `peak_metric`, `locked`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `vga_cal_loop_top.va`, `peak_detector.va`, `gain_controller.va`, `vga_model.va`, `lock_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
