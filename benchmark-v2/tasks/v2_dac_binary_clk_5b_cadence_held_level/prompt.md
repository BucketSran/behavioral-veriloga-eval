# Task: Clocked 5-bit Binary DAC (Renamed Interface)

Implement an EVAS-compatible Verilog-A module that reconstructs an analog held level from a sampled 5-bit binary code.

## Required output file

- `dut.va`

## Module contract

Create module `dac_binary_clk_5b_cadence_held_level` with electrical ports:

- `cadence` (clock input)
- `bit0`, `bit1`, `bit2`, `bit3`, `bit4` (LSB to MSB code inputs)
- `held_level` (analog output)

## Behavior

1. Parameters:
   - `vdd = 1.2`
   - `vss = 0.0`
   - `vth = 0.6`
   - `trise = 1n`
   - `tfall = 1n`
2. On each rising crossing of `cadence` through `vth`, sample `bit0..bit4`.
3. Decode sampled bits as unsigned binary code in `[0,31]`.
4. Convert code to output level:
   - `held_level = vss + (vdd - vss) * code / 31.0`
5. `held_level` must be held between sampling events.
6. Output transition must be smooth.

## Negative constraints

1. Do not implement thermometer decoding.
2. Do not implement continuous combinational follower behavior.
3. Do not use current-domain operators.
