# Ideal ADC 4bit Quantizer

## Task Contract
Implement the Verilog-A DUT `ideal_adc_4bit_quantizer.va` for a clocked ideal differential ADC quantizer with an analog-coded output code.

## Public Verilog-A Interface
Provide `module ideal_adc_4bit_quantizer(vclk, vip, vin, digital);` with electrical inputs `vclk`, `vip`, `vin` and electrical output `digital`.

## Public Parameter Contract
Expose `trise = 20p`, `tfall = 20p`, `tdel = 0`, `vtrans_clk = 0.5`, `vref = 1.0`, and integer `levels = 16` with the ranges declared in the starter file. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `vclk` through `vtrans_clk`, sample the differential input `V(vip) - V(vin)`. Quantize the sample over the symmetric input span from `-vref` to `+vref` using `levels` uniformly spaced output codes, and drive `digital` with the resulting analog code value.

## Modeling Constraints
Use event-driven sampling and `transition` for the code output. Do not continuously track the input between clock edges, use a unipolar range, halve the code scale, or reverse the LSB behavior.

## Output Contract
Submit only the completed Verilog-A module in `ideal_adc_4bit_quantizer.va`.
