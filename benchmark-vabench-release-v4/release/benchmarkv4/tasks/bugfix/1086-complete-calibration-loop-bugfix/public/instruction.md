# Complete Calibration Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `complete_calibration_loop.va`:
  - Module `complete_calibration_loop` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `trim_mon` (output, electrical)
    - position 6: `residual_mon` (output, electrical)

## Public Parameter Contract

- `complete_calibration_loop.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `complete_calibration_loop.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.
- `complete_calibration_loop.target` defaults to `0.45` V; valid range: vmin <= target <= vmax; sets the calibration common-mode target.
- `complete_calibration_loop.loop_gain` defaults to `0.4`; valid range: loop_gain >= 0; sets correction applied to residual error per update.
- `complete_calibration_loop.plant_alpha` defaults to `0.35`; valid range: 0 < plant_alpha <= 1; sets first-order corrected-plant update factor.
- `complete_calibration_loop.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets lower clamp for bounded analog states.
- `complete_calibration_loop.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets upper clamp for bounded analog states.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_TO_TARGET`: restore: Active-high reset initializes out, trim_mon, residual_mon, and metric to their target-state values. Required traces: `time`, `rst`, `out`, `metric`, `trim_mon`, `residual_mon`.
- `P_CLOCKED_LOOP_UPDATE`: restore: After reset releases, calibration state updates on rising clk crossings and holds between updates. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `trim_mon`, `residual_mon`.
- `P_RESIDUAL_OBSERVATION`: restore: Residual_mon exposes clamp(target + raw_error + (trim_mon_next - target), vmin, vmax), where raw_error is V(vin)-target and trim_mon_next is the current edge's bounded negative-feedback trim update. Required traces: `time`, `clk`, `vin`, `trim_mon`, `residual_mon`.
- `P_NEGATIVE_FEEDBACK_DIRECTION`: restore: The trim correction uses trim_mon_next = clamp(trim_mon - loop_gain * residual_before_update, vmin, vmax), so positive residual decreases trim and negative residual increases trim. Required traces: `time`, `clk`, `vin`, `out`, `trim_mon`, `residual_mon`.
- `P_PLANT_CONVERGENCE`: restore: Out follows out_next = clamp(out + plant_alpha * (residual_mon_next - out), vmin, vmax) on each non-reset update. Required traces: `time`, `clk`, `vin`, `out`, `residual_mon`.
- `P_BOUNDS_AND_METRIC`: restore: Bounded analog states remain within vmin through vmax, while metric equals clamp(0.9 - 1.5 * abs(out-target), 0.0, 0.9) after each update. Required traces: `time`, `out`, `metric`, `trim_mon`, `residual_mon`.

## Modeling Constraints

- Use deterministic rising-edge sampled closed-loop calibration state.
- Use bounded state and smoothed voltage contributions only.
- Do not use current contributions, transistor-level devices, continuous-time operators, AC/noise analysis, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `complete_calibration_loop.va`.
Every supplied `.va` file is editable; do not add or omit files.
