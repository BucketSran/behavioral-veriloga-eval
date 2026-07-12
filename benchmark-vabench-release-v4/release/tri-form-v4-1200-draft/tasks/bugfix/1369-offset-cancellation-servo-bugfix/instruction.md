# Offset-cancellation Servo Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `offset_servo_top.va`:
  - Module `offset_servo_top` (entry)
    - position 0: `vinp` (inout, electrical)
    - position 1: `vinn` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `cal_en` (inout, electrical)
    - position 5: `corrected_out` (inout, electrical)
    - position 6: `trim_4` (inout, electrical)
    - position 7: `trim_3` (inout, electrical)
    - position 8: `trim_2` (inout, electrical)
    - position 9: `trim_1` (inout, electrical)
    - position 10: `trim_0` (inout, electrical)
    - position 11: `error_metric` (inout, electrical)
    - position 12: `done` (inout, electrical)
- Artifact `offset_sampler.va`:
  - Module `offset_sampler` (required_submodule)
    - position 0: `vinp` (inout, electrical)
    - position 1: `vinn` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `cal_en` (inout, electrical)
    - position 5: `sampled_error` (inout, electrical)
- Artifact `trim_dac.va`:
  - Module `trim_dac` (required_submodule)
    - position 0: `vinp` (inout, electrical)
    - position 1: `vinn` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `trim_4` (inout, electrical)
    - position 4: `trim_3` (inout, electrical)
    - position 5: `trim_2` (inout, electrical)
    - position 6: `trim_1` (inout, electrical)
    - position 7: `trim_0` (inout, electrical)
    - position 8: `corrected_out` (inout, electrical)
- Artifact `error_integrator.va`:
  - Module `error_integrator` (required_submodule)
    - position 0: `sampled_error` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `cal_en` (inout, electrical)
    - position 4: `trim_4` (inout, electrical)
    - position 5: `trim_3` (inout, electrical)
    - position 6: `trim_2` (inout, electrical)
    - position 7: `trim_1` (inout, electrical)
    - position 8: `trim_0` (inout, electrical)
    - position 9: `error_metric` (inout, electrical)
    - position 10: `done` (inout, electrical)

## Public Parameter Contract

- `offset_servo_top.vdd` defaults to `0.9` V; valid range: finite; overrides logic high output level.
- `offset_servo_top.vss` defaults to `0.0` V; valid range: finite; overrides logic low output level.
- `offset_servo_top.vth` defaults to `0.45` V; valid range: finite; overrides clock/control threshold.
- `offset_servo_top.trim_lsb` defaults to `2e-3` V; valid range: finite positive; overrides offset correction per trim-code step.
- `offset_servo_top.error_tol` defaults to `5e-3` V; valid range: finite positive; overrides residual offset tolerance.
- `offset_servo_top.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `offset_sampler.vss` defaults to `0.0` V; valid range: finite; overrides reset sample level.
- `offset_sampler.vth` defaults to `0.45` V; valid range: finite; overrides clock/control threshold.
- `offset_sampler.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `trim_dac.vdd` defaults to `0.9` V; valid range: finite; overrides logic high output level.
- `trim_dac.vss` defaults to `0.0` V; valid range: finite; overrides logic low output level.
- `trim_dac.vth` defaults to `0.45` V; valid range: finite; overrides trim-bit threshold.
- `trim_dac.trim_lsb` defaults to `2e-3` V; valid range: finite positive; overrides offset correction per trim-code step.
- `trim_dac.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `error_integrator.vdd` defaults to `0.9` V; valid range: finite; overrides logic high output level.
- `error_integrator.vss` defaults to `0.0` V; valid range: finite; overrides logic low output level.
- `error_integrator.vth` defaults to `0.45` V; valid range: finite; overrides clock/control threshold.
- `error_integrator.trim_lsb` defaults to `2e-3` V; valid range: finite positive; overrides offset correction per trim-code step.
- `error_integrator.error_tol` defaults to `5e-3` V; valid range: finite positive; overrides residual offset tolerance.
- `error_integrator.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: On reset, clear trim code, corrected output, error metric, and done; when calibration is disabled, do not advance trim search state. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `corrected_out`, `trim_4`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `error_metric`, `done`.
- `P_TRIM_SEARCH_DIRECTION`: restore: Update the signed 5-bit trim code in the direction that reduces sampled differential error. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `corrected_out`, `trim_4`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `error_metric`, `done`.
- `P_CORRECTED_RESIDUAL`: restore: Drive corrected_out as the differential input minus the signed trim correction. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `corrected_out`, `trim_4`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `error_metric`, `done`.
- `P_ERROR_METRIC`: restore: Expose the current residual offset on error_metric after each enabled trim update. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `corrected_out`, `trim_4`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `error_metric`, `done`.
- `P_DONE_QUALIFICATION`: restore: Assert done only after four consecutive calibration updates with residual magnitude within error_tol. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `corrected_out`, `trim_4`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `error_metric`, `done`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Use voltage contributions for public electrical outputs.
- Do not instantiate transistor-level devices or add testbench, checker, pass/fail, or debug-only ports.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `offset_servo_top.va`, `offset_sampler.va`, `trim_dac.va`, `error_integrator.va`.
Every supplied `.va` file is editable; do not add or omit files.
