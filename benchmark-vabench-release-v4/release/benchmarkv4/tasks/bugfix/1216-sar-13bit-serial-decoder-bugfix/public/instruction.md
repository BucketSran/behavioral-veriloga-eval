# SAR 13bit Serial Decoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_13bit_serial_decoder.va`:
  - Module `sar_13bit_serial_decoder` (entry)
    - position 0: `din` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `ready` (input, electrical)
    - position 3: `dout` (output, electrical)
    - position 4: `dnum` (output, electrical)

## Public Parameter Contract

- `sar_13bit_serial_decoder.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONSUME_ONE_MSB_FIRST_BIT_ON`: restore: Consume one MSB-first bit on each rising `ready` crossing, starting with bit 12 and ending with bit 0. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_ADD_THE_CORRESPONDING_BINARY_WEIGHT_WHEN`: restore: Add the corresponding binary weight when `din` is high. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_INCREMENT_DNUM_FOR_EACH_HIGH_DECISION`: restore: Increment `dnum` for each high decision in the current frame. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_ON_EACH_RISING_CLKS_CROSSING_PUBLISH`: restore: On each rising `clks` crossing, publish the previous frame as a normalized bipolar output. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_MAP_AN_ALL_LOW_FRAME_TO`: restore: Map an all-low frame to `-0.5` and an all-high frame near `+0.5`. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_AFTER_PUBLISHING_RESET_THE_ACCUMULATOR_HIGH`: restore: After publishing, reset the accumulator, high-bit count, and bit pointer for the next frame. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_13bit_serial_decoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
