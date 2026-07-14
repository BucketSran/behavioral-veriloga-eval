# Ideal ADC Out 7bits

## Task Contract
Implement the Verilog-A DUT `ideal_adc_out_7bits_scalar.va` for a fractional 7-input ADC output summarizer.

## Public Verilog-A Interface
Provide `module ideal_adc_out_7bits_scalar(din0, din1, din2, din3, din4, din5, din6, dout);` with electrical inputs `din0` through `din6` and electrical output `dout`.

## Public Parameter Contract
Expose `parameter real vth = 0.45;`. Testbenches may override this threshold.

## Required Behavior
Interpret each input as asserted above `vth`. `din6` through `din2` represent the 16, 8, 4, 2, and 1 unit groups of a nominal 5-bit span, while `din1` and `din0` are half-LSB and quarter-LSB trim groups. Sum the asserted groups and normalize by the nominal 5-bit full-scale span before driving `dout`.

## Modeling Constraints
Use input threshold events and a smooth voltage output. Do not omit the MSB group, reverse LSB/MSB roles, halve the scale, or hard-code a stimulus-specific sequence.

## Output Contract
Submit only the completed Verilog-A module in `ideal_adc_out_7bits_scalar.va`.
