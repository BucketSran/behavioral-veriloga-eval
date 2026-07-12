# DAC Restore 6bit 1p8 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_restore_6bit_1p8.va`:
  - Module `dac_restore_6bit_1p8` (entry)
    - position 0: `d1` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d3` (input, electrical)
    - position 3: `d4` (input, electrical)
    - position 4: `d5` (input, electrical)
    - position 5: `d6` (input, electrical)
    - position 6: `clk` (input, electrical)
    - position 7: `vout` (output, electrical)

## Public Parameter Contract

- `dac_restore_6bit_1p8.vth` defaults to `0.9`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CROSSING_OF_CLK`: restore: On each rising crossing of `clk` through `vth`, sample `d1..d6` and decode an unsigned 6-bit code with weights `32, 16, 8, 4, 2, 1`. Hold the decoded output until the next rising clock event. Map the sampled code to a bipolar 1.8 V mid-rise level: Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.
- `P_TEXT_VOUT_CODE_0_5_3`: restore: ```text vout = (code + 0.5) * 3.6 / 64 - 1.8 ``` Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.
- `P_THE_ALL_ZERO_CODE_THEREFORE_PRODUCES`: restore: The all-zero code therefore produces the lowest half-LSB-centered negative level, and the all-one code produces the highest half-LSB-centered positive level. Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_restore_6bit_1p8.va`.
Every supplied `.va` file is editable; do not add or omit files.
