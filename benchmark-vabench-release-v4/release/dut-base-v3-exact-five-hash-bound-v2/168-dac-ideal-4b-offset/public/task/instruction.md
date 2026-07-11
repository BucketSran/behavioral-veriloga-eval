# DAC Ideal 4b Offset

## Task Contract
Implement the Verilog-A DUT `dac_ideal_4b_offset.va` for an event-updated 4-bit offset DAC.

## Public Verilog-A Interface
Provide `module dac_ideal_4b_offset(din0, din1, din2, din3, dout);` with electrical bit inputs `din0` through `din3` and electrical output `dout`.

## Public Parameter Contract
Expose real parameters `vth = 0.45`, `offset = 0.239`, and `scaling = 32.0 * 10.0 / 9.0`. Testbenches may override these parameters.

## Required Behavior
Interpret `din3` as the MSB and `din0` as the LSB of a 4-bit unsigned code using threshold `vth`. Add the code-scaled trim increment to `offset`, using `scaling` as the public code-to-voltage scale, and drive the result on `dout`.

## Modeling Constraints
Update on input threshold crossings or initial step and drive a smooth voltage output. Do not omit the offset, use the wrong scaling, swap MSB/LSB roles, or hard-code a fixed stimulus sequence.

## Output Contract
Submit only the completed Verilog-A module in `dac_ideal_4b_offset.va`.
