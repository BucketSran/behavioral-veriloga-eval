# L2 CDAC 4b Residue

## Task Contract
Implement the Verilog-A DUT `l2_cdac_4b_residue.va` for a sampled capacitive-DAC residue update flow.

## Public Verilog-A Interface
Provide `module l2_cdac_4b_residue(vin, clks, dctrl1, dctrl2, dctrl3, vres);` with electrical inputs `vin`, `clks`, `dctrl1`, `dctrl2`, `dctrl3` and electrical output `vres`.

## Public Parameter Contract
Expose real parameters `vdd = 1`, `vrefp = 1`, and `vrefn = 0`. Testbenches may override these parameters.

## Required Behavior
Sample `vin` into the residue level on the initial step and on each falling crossing of `clks` through `vdd/2`. Add capacitive reference steps to the held residue on rising crossings of the control inputs: `dctrl3` adds one-half of the reference span, `dctrl2` adds one-quarter, and `dctrl1` adds one-eighth.

## Modeling Constraints
Use event-driven sampling and retained residue state. Do not sample on the wrong clock edge, subtract the control steps, use the wrong MSB step size, or continuously recompute the residue from the controls.

## Output Contract
Submit only the completed Verilog-A module in `l2_cdac_4b_residue.va`.
