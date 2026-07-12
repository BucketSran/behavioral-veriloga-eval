# DAC Restore 10bit Offset Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_restore_10bit_offset.va`:
  - Module `dac_restore_10bit_offset` (entry)
    - position 0: `D1` (input, electrical)
    - position 1: `D2` (input, electrical)
    - position 2: `D3` (input, electrical)
    - position 3: `D4` (input, electrical)
    - position 4: `D5` (input, electrical)
    - position 5: `D6` (input, electrical)
    - position 6: `D7` (input, electrical)
    - position 7: `D8` (input, electrical)
    - position 8: `D9` (input, electrical)
    - position 9: `D10` (input, electrical)
    - position 10: `D0` (input, electrical)
    - position 11: `clk` (input, electrical)
    - position 12: `vout` (output, electrical)

## Public Parameter Contract

- `dac_restore_10bit_offset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dac_restore_10bit_offset.lsb` defaults to `1.8 / 1024.0`; valid range: finite; overrides lsb.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_CODE_SAMPLING`: restore: Only rising crossings of `clk` through `vth` update the held DAC output; input-bit changes between clock crossings do not alter `vout`. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_WEIGHTED_REDUNDANT_CODE`: restore: `D10` is the largest weight, `D0` is the LSB, and `D6` and `D7` both contribute the redundant 64-LSB weight before scaling. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_OFFSET_MIDRISE_OUTPUT`: restore: The asserted weighted code is shifted by the source -32 LSB offset and placed at the mid-rise half-LSB output level using the public `lsb` scale. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_OUTPUT_SMOOTH_HOLD`: restore: `vout` transitions smoothly to each sampled code value and holds that value until the next qualifying clock edge. Required traces: `time`, `clk`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_restore_10bit_offset.va`.
Every supplied `.va` file is editable; do not add or omit files.
