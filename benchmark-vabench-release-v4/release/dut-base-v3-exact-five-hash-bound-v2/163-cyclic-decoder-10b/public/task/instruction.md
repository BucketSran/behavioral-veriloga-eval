# Cyclic Decoder 10b

## Task Contract
Implement the Verilog-A DUT `cyclic_decoder_10b.va` for a serial cyclic ADC decision decoder with full-weight and half-weight decision states.

## Public Verilog-A Interface
Provide `module cyclic_decoder_10b(dp, dn, ready, clks, dout);` with electrical inputs `dp`, `dn`, `ready`, `clks` and electrical output `dout`.

## Public Parameter Contract
Expose real parameter `vth = 0.55` and integer parameter `nbit = 10`. Testbenches may override these parameters.

## Required Behavior
After each publication clock, collect up to `nbit` serial decisions on rising `ready` crossings, MSB first. A high `dp` adds the full current binary weight. If `dp` is low and `dn` is high, add half of the current binary weight. On each rising `clks` crossing, publish the accumulated value normalized to the `nbit` full-scale range and centered by subtracting 0.5, then reset the accumulator.

## Modeling Constraints
Use event-driven ready and clock handling. Do not omit the `dn` half-weight state, use the wrong denominator, omit the midscale offset, or continuously update from the decision pins.

## Output Contract
Submit only the completed Verilog-A module in `cyclic_decoder_10b.va`.
