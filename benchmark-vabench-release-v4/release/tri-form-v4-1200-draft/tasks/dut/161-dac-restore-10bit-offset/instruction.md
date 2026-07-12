# DAC Restore 10bit Offset

## Task Contract
Implement the Verilog-A DUT `dac_restore_10bit_offset.va` for a clocked source-specific 10-bit offset DAC reconstruction.

## Public Verilog-A Interface
Provide `module dac_restore_10bit_offset(D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D0, clk, vout);` with electrical bit inputs `D0` through `D10`, clock input `clk`, and electrical output `vout`.

## Public Parameter Contract
Expose real parameters `vth = 0.45` and `lsb = 1.8 / 1024.0`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clk` through `vth`, reconstruct the source offset DAC code. `D10` is the largest weight, `D0` is the LSB, and `D6` and `D7` both contribute the same 64-LSB redundant weight. After summing the asserted weights, apply the source code offset of -32 LSBs and use a mid-rise half-LSB output placement around the bipolar 1.8 V span.

## Modeling Constraints
Use clocked code reconstruction and `transition` for `vout`. Do not omit the code offset, remove the duplicated 64-LSB contribution, use the wrong LSB scale, or continuously track input bit changes.

## Output Contract
Submit only the completed Verilog-A module in `dac_restore_10bit_offset.va`.
