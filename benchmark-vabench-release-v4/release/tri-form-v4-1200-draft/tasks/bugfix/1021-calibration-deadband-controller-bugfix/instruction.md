# Calibration Deadband Controller Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `calibration_deadband_controller.va`:
  - Module `calibration_deadband_controller` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `calibration_deadband_controller.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `calibration_deadband_controller.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.
- `calibration_deadband_controller.target` defaults to `0.45` V; valid range: vmin <= target <= vmax; sets initial, reset, and zero-error trim target.
- `calibration_deadband_controller.deadband` defaults to `0.05` V; valid range: deadband >= 0; sets the symmetric no-update error interval.
- `calibration_deadband_controller.step_size` defaults to `0.06` V; valid range: step_size > 0; sets trim increment or decrement per accepted update.
- `calibration_deadband_controller.vmin` defaults to `0.05` V; valid range: vmin <= target and vmin < vmax; sets lower output clamp.
- `calibration_deadband_controller.vmax` defaults to `0.85` V; valid range: vmax >= target and vmax > vmin; sets upper output clamp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_RESET_TARGET`: restore: Out initializes to target and returns to target while rst is above vth; metric is low during reset. Required traces: `time`, `rst`, `out`, `metric`.
- `P_POSITIVE_ERROR_STEP`: restore: At a rising clock crossing with vin minus target greater than deadband, out increases by one step_size and metric goes high. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_NEGATIVE_ERROR_STEP`: restore: At a rising clock crossing with vin minus target less than negative deadband, out decreases by one step_size and metric goes high. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_DEADBAND_HOLD`: restore: At a rising clock crossing with signed error inside the inclusive deadband, out holds and metric remains low. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_OUTPUT_CLAMP`: restore: Repeated updates cannot drive out below vmin or above vmax. Required traces: `time`, `clk`, `vin`, `out`.
- `P_BETWEEN_EDGE_HOLD`: restore: Out state does not follow vin between rising clock crossings. Required traces: `time`, `clk`, `vin`, `out`.

## Modeling Constraints

- Use deterministic rising-edge sampled state updates.
- Use voltage contributions only.
- Do not use current contributions, transistor-level devices, AC/noise analysis, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `calibration_deadband_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
