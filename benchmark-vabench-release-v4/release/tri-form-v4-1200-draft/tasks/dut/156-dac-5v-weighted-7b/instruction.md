# DAC 5V Weighted 7b

## Task Contract
Implement the Verilog-A DUT `dac_5v_weighted_7b.va` for a clocked 7-bit binary-weighted DAC with a fixed terminating reference contribution.

## Public Verilog-A Interface
Provide `module dac_5v_weighted_7b(clks, din0, din1, din2, din3, din4, din5, din6, vout);` with electrical clock input `clks`, electrical bit inputs `din0` through `din6`, and electrical output `vout`.

## Public Parameter Contract
Expose real parameters `vth = 0.75`, `tt = 200p`, `delay = 1n`, `refp = 5`, and `refn = 1` with the ranges declared in the starter file. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clks` through `vth`, evaluate a 7-bit binary-weighted DAC where `din0` is the largest weight and `din6` is the smallest switched weight. Each bit selects `refp` for high and `refn` for low at its binary fraction. Include the fixed terminating LSB contribution tied to `refn`, then drive the held DAC output.

## Modeling Constraints
Use clocked sampling, weighted voltage contributions, and the public output transition delay. Do not omit the MSB contribution, drop the fixed termination, use the wrong low reference, or halve the output scale.

## Output Contract
Submit only the completed Verilog-A module in `dac_5v_weighted_7b.va`.
