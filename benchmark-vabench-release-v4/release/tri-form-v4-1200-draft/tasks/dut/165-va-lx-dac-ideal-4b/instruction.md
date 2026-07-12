# VA LX DAC Ideal 4b

## Task Contract
Implement the Verilog-A DUT `va_lx_dac_ideal_4b.va` for a ready-clocked unipolar 4-bit DAC.

## Public Verilog-A Interface
Provide `module va_lx_dac_ideal_4b(din1, din2, din3, din4, rdy, aout);` with electrical bit inputs `din1` through `din4`, ready input `rdy`, and electrical output `aout`.

## Public Parameter Contract
Expose real parameters `vdd = 1.8` and `vth = 0.9`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `rdy` through `vth`, decode `din4` as the MSB and `din1` as the LSB of a 4-bit unipolar binary fraction. Scale the fraction by `vdd` and hold the result on `aout`.

## Modeling Constraints
Use clocked code sampling and `transition` for the output. Do not omit the `vdd` scale, reverse MSB/LSB weights, ignore the LSB, or continuously track input bit changes.

## Output Contract
Submit only the completed Verilog-A module in `va_lx_dac_ideal_4b.va`.
