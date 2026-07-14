# Reference Flash 8level Decoder

## Task Contract
Implement the Verilog-A DUT `ref_flash_8level_decoder.va` for an 8-level reference flash decoder with a residue output.

## Public Verilog-A Interface
Provide `module ref_flash_8level_decoder(vin, dt0, dt1, dt2, dt3, dt4, dt5, dt6, dt7, clks, dout, vres);` with electrical input `vin`, tap inputs `dt0` through `dt7`, clock input `clks`, and electrical outputs `dout`, `vres`.

## Public Parameter Contract
Expose real parameters `vth = 0.45`, `tt = 10p`, and `vref = 1`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clks` through `vth`, count the asserted flash taps. Drive `dout` with the count divided by eight. Drive `vres` with the sampled `vin` minus the centered tap count scaled by `vref/8`.

## Modeling Constraints
Use clocked tap counting and retained output values. Do not use the wrong count normalization, leave the residue uncentered, ignore upper taps, or continuously track taps between clocks.

## Output Contract
Submit only the completed Verilog-A module in `ref_flash_8level_decoder.va`.
