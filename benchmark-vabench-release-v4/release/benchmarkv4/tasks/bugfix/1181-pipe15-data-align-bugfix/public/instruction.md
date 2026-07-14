# Pipe15 Data Align Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pipe15_data_align.va`:
  - Module `pipe15_data_align` (entry)
    - position 0: `samp` (input, electrical)
    - position 1: `d0` (input, electrical)
    - position 2: `d1` (input, electrical)
    - position 3: `d2` (input, electrical)
    - position 4: `d3` (input, electrical)
    - position 5: `d4` (input, electrical)
    - position 6: `d5` (input, electrical)
    - position 7: `d6` (input, electrical)
    - position 8: `d7` (input, electrical)
    - position 9: `d8` (input, electrical)
    - position 10: `d9` (input, electrical)
    - position 11: `d10` (input, electrical)
    - position 12: `d11` (input, electrical)
    - position 13: `d12` (input, electrical)
    - position 14: `d13` (input, electrical)
    - position 15: `d14` (input, electrical)
    - position 16: `do0` (output, electrical)
    - position 17: `do1` (output, electrical)
    - position 18: `do2` (output, electrical)
    - position 19: `do3` (output, electrical)
    - position 20: `do4` (output, electrical)
    - position 21: `do5` (output, electrical)
    - position 22: `do6` (output, electrical)
    - position 23: `do7` (output, electrical)
    - position 24: `do8` (output, electrical)
    - position 25: `do9` (output, electrical)
    - position 26: `do10` (output, electrical)
    - position 27: `do11` (output, electrical)
    - position 28: `do12` (output, electrical)
    - position 29: `do13` (output, electrical)
    - position 30: `do14` (output, electrical)

## Public Parameter Contract

- `pipe15_data_align.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pipe15_data_align.tt` defaults to `20p`; valid range: finite; overrides tt.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLE_ON_RISING_SAMP`: restore: On each rising `samp` crossing, sample all fifteen input bits `d0..d14` into the alignment pipeline. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_ZERO_DELAY_OUTPUT_GROUP`: restore: Outputs `do0..do2` publish the current sampled values without an added sample delay. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_STAGGERED_DELAY_OUTPUT_GROUPS`: restore: Outputs `do3..do6`, `do7..do10`, and `do11..do14` publish the one-, two-, and three-sample delayed input groups respectively. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_VOLTAGE_CODED_OUTPUT_LEVELS`: restore: Every aligned output is driven as a voltage-coded logic level near 0 V or `vdd` with the declared transition timing. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pipe15_data_align.va`.
Every supplied `.va` file is editable; do not add or omit files.
