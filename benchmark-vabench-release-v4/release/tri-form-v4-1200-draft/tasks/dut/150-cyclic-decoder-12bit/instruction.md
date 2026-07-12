# Cyclic Decoder 12bit

## Task Contract
Implement the Verilog-A DUT `cyclic_decoder_12bit.va` for a clocked 12-bit unsigned decision decoder with a centered analog output.

## Public Verilog-A Interface
Provide `module cyclic_decoder_12bit(d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, clks, dout);` with electrical inputs `d0` through `d11`, clock input `clks`, and electrical output `dout`.

## Public Parameter Contract
Expose `parameter real vth = 0.55;`. Testbenches may override this threshold.

## Required Behavior
On each rising crossing of `clks` through `vth`, decode `d0` as the LSB and `d11` as the MSB of a 12-bit unsigned code. Normalize the code to the full 12-bit range and subtract 0.5 before driving `dout`.

## Modeling Constraints
Use clocked sampling and `transition` for the output. Do not reverse bit weights, omit the midscale offset, halve the output scale, or continuously track input changes between clocks.

## Output Contract
Submit only the completed Verilog-A module in `cyclic_decoder_12bit.va`.
