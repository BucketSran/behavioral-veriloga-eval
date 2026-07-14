# Four Channel Edge Sampler

## Task Contract
Implement the Verilog-A DUT `four_channel_edge_sampler.va` for simultaneous sampling of four analog channels on a configurable clock edge.

## Public Verilog-A Interface
Provide `module four_channel_edge_sampler(clk, vin0, vin1, vin2, vin3, vout0, vout1, vout2, vout3);` with electrical input `clk`, electrical inputs `vin0` through `vin3`, and electrical outputs `vout0` through `vout3`.

## Public Parameter Contract
Expose integer `direction = 1` and real parameters `vdd = 1.2`, `tr = 50p`, `tf = 50p`, and `td = 0`. Testbenches may override these parameters.

## Required Behavior
On the configured crossing direction of `clk` through `vdd/2`, simultaneously sample `vin0` through `vin3` and hold the sampled values on the matching outputs until the next sampling event.

## Modeling Constraints
Use event-driven sampling and retained channel registers. Do not swap channels, leave one channel stuck at its initial value, apply half output gain, or continuously track the inputs.

## Output Contract
Submit only the completed Verilog-A module in `four_channel_edge_sampler.va`.
