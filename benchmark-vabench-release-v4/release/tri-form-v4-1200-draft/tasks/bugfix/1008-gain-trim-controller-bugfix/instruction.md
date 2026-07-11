# Gain Trim Controller Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `gain_trim_controller.va`:
  - Module `gain_trim_controller` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `meas` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `gain_ctrl` (output, electrical)

## Public Parameter Contract

- `gain_trim_controller.vth` defaults to `0.45` V; valid range: vth > 0; sets clk and rst decision threshold.
- `gain_trim_controller.tr` defaults to `5e-10` s; valid range: tr > 0; sets gain_ctrl transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_RESET`: restore: gain_ctrl initializes to 0.30 V and returns to 0.30 V on a rising clk edge while rst is high. Required traces: `time`, `clk`, `rst`, `gain_ctrl`.
- `P_ERROR_DIRECTION`: restore: On rising clk edges, gain_ctrl increases by 0.05 V below target-0.02 V and decreases by 0.05 V above target+0.02 V. Required traces: `time`, `clk`, `rst`, `meas`, `target`, `gain_ctrl`.
- `P_DEADBAND_HOLD`: restore: gain_ctrl holds when meas is within the inclusive target deadband. Required traces: `time`, `clk`, `meas`, `target`, `gain_ctrl`.
- `P_CONTROL_CLAMP`: restore: gain_ctrl remains within the inclusive 0.05 V to 0.85 V range. Required traces: `time`, `gain_ctrl`.

## Modeling Constraints

- Use deterministic voltage-domain behavior.
- Update state only on rising clk crossings and drive gain_ctrl with finite transition smoothing.
- Do not hard-code evaluator stimulus or sample times.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `gain_trim_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
