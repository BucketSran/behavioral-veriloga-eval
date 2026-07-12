# Onehot Progress Encoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `onehot_progress_encoder.va`:
  - Module `onehot_progress_encoder` (entry)
    - position 0: `ck` (input, electrical)
    - position 1: `d0` (output, electrical)
    - position 2: `d1` (output, electrical)
    - position 3: `d2` (output, electrical)
    - position 4: `d3` (output, electrical)
    - position 5: `d4` (output, electrical)
    - position 6: `d5` (output, electrical)
    - position 7: `d6` (output, electrical)
    - position 8: `d7` (output, electrical)
    - position 9: `d8` (output, electrical)
    - position 10: `d9` (output, electrical)
    - position 11: `d10` (output, electrical)
    - position 12: `d11` (output, electrical)
    - position 13: `d12` (output, electrical)
    - position 14: `d13` (output, electrical)
    - position 15: `d14` (output, electrical)
    - position 16: `d15` (output, electrical)
    - position 17: `sum` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PROGRESS_INITIAL_STATE`: restore: All progress outputs and the count initialize to zero. Required traces: `time`, `ck`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `sum`.
- `P_SEQUENTIAL_ONEHOT_ASSERTION`: restore: Each rising `ck` crossing asserts the next progress bit in order from `d0` through `d15` without skipping the first bit. Required traces: `time`, `ck`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`.
- `P_ACCUMULATING_PROGRESS_BITS`: restore: Previously asserted progress bits remain high until all sixteen bits have been asserted. Required traces: `time`, `ck`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`.
- `P_SUM_COUNT_OUTPUT`: restore: `sum` reports the current count value corresponding to the number of asserted progress bits. Required traces: `time`, `ck`, `sum`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `onehot_progress_encoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
