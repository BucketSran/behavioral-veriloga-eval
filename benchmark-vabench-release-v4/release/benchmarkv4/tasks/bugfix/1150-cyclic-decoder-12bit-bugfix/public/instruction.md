# Cyclic Decoder 12bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cyclic_decoder_12bit.va`:
  - Module `cyclic_decoder_12bit` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `d4` (input, electrical)
    - position 5: `d5` (input, electrical)
    - position 6: `d6` (input, electrical)
    - position 7: `d7` (input, electrical)
    - position 8: `d8` (input, electrical)
    - position 9: `d9` (input, electrical)
    - position 10: `d10` (input, electrical)
    - position 11: `d11` (input, electrical)
    - position 12: `clks` (input, electrical)
    - position 13: `dout` (output, electrical)

## Public Parameter Contract

- `cyclic_decoder_12bit.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_12BIT_DECODE`: restore: Each rising `clks` crossing samples the twelve voltage-coded bits into an unsigned code. Required traces: `time`, `clks`, `d0`, `d1`, `d10`, `d11`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `dout`.
- `P_BIT_WEIGHT_ORDER`: restore: `d0` is the LSB and `d11` is the MSB in the decoded code. Required traces: `time`, `clks`, `d0`, `d1`, `d10`, `d11`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `dout`.
- `P_CENTERED_OUTPUT_SCALE`: restore: The decoded value is normalized to the full 12-bit range, shifted by the half-scale midpoint, and held on `dout`. Required traces: `time`, `clks`, `d0`, `d1`, `d10`, `d11`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cyclic_decoder_12bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
