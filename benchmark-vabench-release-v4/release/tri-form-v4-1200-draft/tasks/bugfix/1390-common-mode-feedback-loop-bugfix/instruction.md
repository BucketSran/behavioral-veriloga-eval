# Common-mode Feedback Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cmfb_loop_top.va`:
  - Module `cmfb_loop_top` (entry)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `vop_out` (output, electrical)
    - position 6: `von_out` (output, electrical)
    - position 7: `trim_2` (output, electrical)
    - position 8: `trim_1` (output, electrical)
    - position 9: `trim_0` (output, electrical)
    - position 10: `cm_error` (output, electrical)
    - position 11: `locked` (output, electrical)
- Artifact `cm_sensor.va`:
  - Module `cm_sensor` (required_submodule)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `cm_error_raw` (output, electrical)
- Artifact `trim_controller.va`:
  - Module `trim_controller` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `cm_error_raw` (input, electrical)
    - position 4: `trim_2` (output, electrical)
    - position 5: `trim_1` (output, electrical)
    - position 6: `trim_0` (output, electrical)
    - position 7: `trim_corr` (output, electrical)
    - position 8: `locked` (output, electrical)
- Artifact `output_balancer.va`:
  - Module `output_balancer` (required_submodule)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `trim_corr` (input, electrical)
    - position 5: `vop_out` (output, electrical)
    - position 6: `von_out` (output, electrical)
    - position 7: `cm_error` (output, electrical)

## Public Parameter Contract

- `cmfb_loop_top.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `cmfb_loop_top.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `cmfb_loop_top.vcm` defaults to `0.45` V; valid range: vss < vcm < vdd; sets the target common mode.
- `cmfb_loop_top.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `cmfb_loop_top.trim_lsb` defaults to `0.01` V; valid range: trim_lsb > 0; sets one unsigned trim correction step.
- `cmfb_loop_top.lock_tol` defaults to `0.01` V; valid range: lock_tol >= 0; sets the residual-error lock tolerance.
- `cmfb_loop_top.tr` defaults to `2e-10` s; valid range: tr > 0; sets output transition smoothing.
- `cm_sensor.vcm` defaults to `0.45` V; valid range: finite; sets target common mode.
- `cm_sensor.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.
- `trim_controller.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `trim_controller.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `trim_controller.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `trim_controller.trim_lsb` defaults to `0.01` V; valid range: trim_lsb > 0; sets one correction step.
- `trim_controller.lock_tol` defaults to `0.01` V; valid range: lock_tol >= 0; sets lock tolerance.
- `trim_controller.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.
- `output_balancer.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `output_balancer.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `output_balancer.vcm` defaults to `0.45` V; valid range: vss < vcm < vdd; sets target common mode.
- `output_balancer.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `output_balancer.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disable clears trim and lock, reports zero residual error, and bypasses correction. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_COMMON_MODE_ERROR`: restore: The reported common-mode error equals the corrected output average minus vcm. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_TRIM_DIRECTION`: restore: At enabled rising clock edges the bounded unsigned trim code moves in the direction that reduces representable positive common-mode error. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_DIFFERENTIAL_PRESERVATION`: restore: Common-mode correction preserves input differential polarity and differential magnitude unless a supply clamp is reached. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_LOCK_QUALIFICATION`: restore: Lock asserts only after two consecutive enabled updates within lock_tol. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cmfb_loop_top.va`, `cm_sensor.va`, `trim_controller.va`, `output_balancer.va`.
Every supplied `.va` file is editable; do not add or omit files.
