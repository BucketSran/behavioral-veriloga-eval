# Task: Clocked 6-bit Binary DAC (Renamed Interface)

Implement an EVAS-compatible Verilog-A module that reconstructs an analog held output from a sampled 6-bit binary code.

## Required output file

- `dut.va`

## Module contract

Create module `dac_binary_clk_6b_refclk_recon_level` with electrical ports:

- `refclk` (clock input)
- `b0`, `b1`, `b2`, `b3`, `b4`, `b5` (LSB to MSB code inputs)
- `recon_level` (analog output)

## Behavior

1. Parameters:
   - `vdd = 1.2`
   - `vss = 0.0`
   - `vth = 0.6`
   - `trise = 1n`
   - `tfall = 1n`
2. On each rising crossing of `refclk` through `vth`, sample `b0..b5`.
3. Decode sampled bits as unsigned binary code in `[0,63]`.
4. Convert code to output:
   - `recon_level = vss + (vdd - vss) * code / 63.0`
5. Output is held between sampling events.
6. Use smooth transition output update.

## Negative constraints

1. Do not use thermometer decoding.
2. Do not use continuous follower behavior.
3. Do not use current-domain operators.
