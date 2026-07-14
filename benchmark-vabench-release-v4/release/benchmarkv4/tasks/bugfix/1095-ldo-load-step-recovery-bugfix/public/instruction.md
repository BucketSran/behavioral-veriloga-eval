# LDO Load Step Recovery Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ldo_load_step_recovery_flow.va`:
  - Module `ldo_load_step_recovery_flow` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `load_mon` (output, electrical)
    - position 6: `ctrl_mon` (output, electrical)

## Public Parameter Contract

- `ldo_load_step_recovery_flow.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `ldo_load_step_recovery_flow.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_REGULATION_STATE`: restore: Active-high reset initializes out and target to 0.60 V, load_mon to 0.10 V, ctrl_mon to 0.50 V, metric to 0.9 V, and clears recovery progress. Required traces: `time`, `rst`, `out`, `metric`, `load_mon`, `ctrl_mon`.
- `P_BOUNDED_LOAD_AND_TARGET`: restore: Each non-reset rising clk edge clips vin to 0 V through 0.9 V on load_mon and uses the public load-dependent target 0.61 V minus 0.025 times load. Required traces: `time`, `clk`, `rst`, `vin`, `load_mon`, `out`.
- `P_CONTROL_MONITOR`: restore: Ctrl_mon represents the public load and regulation-error control expression and remains clamped to 0.05 V through 0.85 V. Required traces: `time`, `clk`, `load_mon`, `out`, `ctrl_mon`.
- `P_HEAVY_LOAD_DROOP`: restore: A sampled load increase greater than 0.20 V causes the public 0.13 V transient droop before first-order recovery and restarts recovery qualification. Required traces: `time`, `clk`, `load_mon`, `out`, `metric`.
- `P_LIGHT_LOAD_KICK`: restore: A sampled load decrease greater than 0.20 V causes the public 0.05 V light-load recovery kick before first-order recovery and restarts qualification. Required traces: `time`, `clk`, `load_mon`, `out`, `metric`.
- `P_RECOVERY_AND_SETTLING`: restore: Every non-reset update applies the public 0.30 first-order recovery, clamps out to 0.20 V through 0.75 V, and sets metric high only after at least five updates with target error below 0.045 V. Required traces: `time`, `clk`, `out`, `metric`, `load_mon`.

## Modeling Constraints

- Use deterministic rising-edge sampled load-step and recovery state.
- Use bounded smoothed voltage contributions only.
- Do not use branch-current contributions, transistor-level devices, AC/noise analysis, KCL/KVL regulation loops, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ldo_load_step_recovery_flow.va`.
Every supplied `.va` file is editable; do not add or omit files.
