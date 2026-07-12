# Bin2ther 2b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bin2ther_2b.va`:
  - Module `bin2ther_2b` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `gnd` (input, electrical)
    - position 2: `b1` (input, electrical)
    - position 3: `b0` (input, electrical)
    - position 4: `t0` (output, electrical)
    - position 5: `t1` (output, electrical)
    - position 6: `t2` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INTERPRET_B1_AND_B0_RELATIVE_TO`: restore: Interpret `b1` and `b0` relative to the local rail midpoint. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_T0_AND_T1_HIGH_TOGETHER`: restore: Drive `t0` and `t1` high together when `b1` is high. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_T2_HIGH_WHEN_B0_IS`: restore: Drive `t2` high when `b0` is high. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_EACH_LOW_OUTPUT_TO_THE`: restore: Drive each low output to the local `gnd` rail and each high output to the local `vdd` rail. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bin2ther_2b.va`.
Every supplied `.va` file is editable; do not add or omit files.
