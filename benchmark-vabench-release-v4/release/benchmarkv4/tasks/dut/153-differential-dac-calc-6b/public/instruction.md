# Differential DAC Calc 6b

## Task Contract
Implement the Verilog-A DUT `differential_dac_calc_6b.va` for a clocked complementary 6-bit weighted DAC calculation.

## Public Verilog-A Interface
Provide `module differential_dac_calc_6b(din0, din1, din2, din3, din4, din5, clks, voutp, voutn);` with electrical inputs `din0` through `din5`, clock input `clks`, and electrical outputs `voutp`, `voutn`.

## Public Parameter Contract
Expose real parameters `vth = 0.75`, `vcm = 0.75`, `refp = 0.925`, `refn = 0.575`, `tt = 200p`, and `convdelay = 1n`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clks` through `vth`, decode `din0` as the largest binary-weighted decision and `din5` as the smallest. For `voutp`, each high bit selects the corresponding weighted contribution from `refp` and each low bit selects `refn`; `voutn` uses the complementary selections. Include the common-mode termination contribution so the two outputs remain centered around `vcm`.

## Modeling Constraints
Use event-driven code sampling, complementary weighted sums, and `transition` with the public delay and edge parameters. Do not invert the differential outputs, reverse the MSB weight, omit the termination term, or halve the output swing.

## Output Contract
Submit only the completed Verilog-A module in `differential_dac_calc_6b.va`.
