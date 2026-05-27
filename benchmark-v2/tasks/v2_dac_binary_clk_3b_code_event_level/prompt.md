# Task: Clocked 3-bit Binary DAC (Event-Rename Variant)

Implement an EVAS-compatible Verilog-A module that reconstructs an analog output level from sampled 3-bit binary code.

## Required output file

- `dut.va`

## Module contract

Create module `dac_binary_clk_3b_code_event_level` with electrical ports:

- `code_event` (clock input)
- `c0`, `c1`, `c2` (LSB to MSB code inputs)
- `out_level` (analog output)

## Behavior

1. Parameters:
   - `vdd = 1.2`
   - `vss = 0.0`
   - `vth = 0.6`
   - `trise = 1n`
   - `tfall = 1n`
2. On each rising crossing of `code_event` through `vth`, sample `c0..c2`.
3. Decode sampled bits as unsigned binary code in `[0,7]`.
4. Convert code to output:
   - `out_level = vss + (vdd - vss) * code / 7.0`
5. Output is held between events.
6. Use smooth transition output update.

## Negative constraints

1. Do not use thermometer decoding.
2. Do not use continuous follower behavior.
3. Do not use current-domain operators.
