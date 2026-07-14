# Trim Calibration Controller Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cdac_calibration.va`:
  - Module `cdac_calibration` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `err` (input, electrical)
    - position 3: `trim` (output, electrical)

## Public Parameter Contract

- `cdac_calibration.vth` defaults to `0.45` V; valid range: vth > 0; sets clk, rst, and err decision threshold.
- `cdac_calibration.tr` defaults to `5e-10` s; valid range: tr > 0; sets trim transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_RESET`: restore: trim initializes to 0.45 V and returns to 0.45 V on a rising clk edge while rst is high. Required traces: `time`, `clk`, `rst`, `trim`.
- `P_CLOCKED_STEP`: restore: Each rising clk edge outside reset adds 0.06 V for high err and subtracts 0.06 V for low err. Required traces: `time`, `clk`, `rst`, `err`, `trim`.
- `P_TRIM_CLAMP`: restore: trim is clamped to the inclusive 0.05 V to 0.85 V range. Required traces: `time`, `trim`.
- `P_CLOCKED_HOLD`: restore: trim holds its state between rising clk updates. Required traces: `time`, `clk`, `trim`.

## Modeling Constraints

- Use deterministic voltage-domain behavior.
- Drive trim with a finite smoothed voltage contribution.
- Do not hard-code evaluator stimulus or sample times.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cdac_calibration.va`.
Every supplied `.va` file is editable; do not add or omit files.
