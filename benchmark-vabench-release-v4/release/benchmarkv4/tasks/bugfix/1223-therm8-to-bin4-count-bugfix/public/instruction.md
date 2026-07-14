# Therm8 To Bin4 Count Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `therm8_to_bin4_count.va`:
  - Module `therm8_to_bin4_count` (entry)
    - position 0: `th0` (input, electrical)
    - position 1: `th1` (input, electrical)
    - position 2: `th2` (input, electrical)
    - position 3: `th3` (input, electrical)
    - position 4: `th4` (input, electrical)
    - position 5: `th5` (input, electrical)
    - position 6: `th6` (input, electrical)
    - position 7: `th7` (input, electrical)
    - position 8: `b0` (output, electrical)
    - position 9: `b1` (output, electrical)
    - position 10: `b2` (output, electrical)
    - position 11: `b3` (output, electrical)

## Public Parameter Contract

- `therm8_to_bin4_count.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_COUNT_HOW_MANY_OF_TH0_TH7`: restore: Count how many of `th0..th7` are above `vth`. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_ENCODE_THE_COUNT_AS_A_4`: restore: Encode the count as a 4-bit binary word. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_DRIVE_B0_B3_AS_VOLTAGE_CODED`: restore: Drive `b0..b3` as voltage-coded outputs with `b0` as the least significant bit. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_SUPPORT_ANY_INPUT_PATTERN_BY_COUNTING`: restore: Support any input pattern by counting high inputs rather than assuming a perfectly monotonic thermometer prefix. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `therm8_to_bin4_count.va`.
Every supplied `.va` file is editable; do not add or omit files.
