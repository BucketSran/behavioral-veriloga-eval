# Reference Flash 15level Decoder

## Task Contract
Implement the Verilog-A DUT `ref_flash_15level_decoder.va` for a clocked 15-tap flash thermometer fraction decoder.

## Public Verilog-A Interface
Provide `module ref_flash_15level_decoder(dt0, dt1, dt2, dt3, dt4, dt5, dt6, dt7, dt8, dt9, dt10, dt11, dt12, dt13, dt14, clks, dout);` with electrical tap inputs `dt0` through `dt14`, clock input `clks`, and electrical output `dout`.

## Public Parameter Contract
Expose real parameters `vth = 0.45` and `tt = 10p`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clks` through `vth`, count how many of the 15 tap inputs are above `vth`, divide the count by 15, and hold the fraction on `dout`.

## Modeling Constraints
Use clocked thermometer counting and `transition` on the output. Do not ignore upper taps, use the wrong normalization, halve the output gain, or continuously track inputs between clocks.

## Output Contract
Submit only the completed Verilog-A module in `ref_flash_15level_decoder.va`.
