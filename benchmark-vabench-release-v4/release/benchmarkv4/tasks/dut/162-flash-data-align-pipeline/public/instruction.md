# Flash Data Align Pipeline

## Task Contract
Implement the Verilog-A DUT `flash_data_align_pipeline.va` for a clocked flash thermometer count alignment pipeline.

## Public Verilog-A Interface
Provide `module flash_data_align_pipeline(clk, din0, din1, din2, din3, din4, din5, din6, din7, dout0, dout1, dout2, dout3);` with electrical clock input `clk`, thermometer inputs `din0` through `din7`, and electrical outputs `dout0` through `dout3`.

## Public Parameter Contract
Expose `parameter real vth = 0.45;`. Testbenches may override this threshold.

## Required Behavior
On each rising crossing of `clk` through `vth`, count the eight asserted thermometer inputs and shift that count through a four-stage alignment pipeline. Drive `dout0` as the LSB and `dout3` as the MSB of the delayed count.

## Modeling Constraints
Use event-driven pipeline registers and voltage-coded output bits. Do not reduce the delay to three cycles, ignore upper thermometer inputs, swap output bit order, or continuously track the current count.

## Output Contract
Submit only the completed Verilog-A module in `flash_data_align_pipeline.va`.
