# Ideal DAC 4bit Differential

## Task Contract
Implement the Verilog-A DUT `ideal_dac_4bit_differential.va` for a clocked ideal differential DAC with a supplied output common-mode voltage.

## Public Verilog-A Interface
Provide `module ideal_dac_4bit_differential(clk, digital, vcm, vop, von);` with electrical inputs `clk`, `digital`, `vcm` and electrical outputs `vop`, `von`.

## Public Parameter Contract
Expose `trise = 20p`, `tfall = 20p`, `tdel = 0`, `vref = 1.0`, `vtrans_clk = 0.5`, and integer `levels = 16` with the ranges declared in the starter file. Testbenches may override these parameters.

## Required Behavior
On each falling crossing of `clk` through `vtrans_clk`, sample the analog code on `digital`, clamp it into the valid code range, and convert it to a mid-rise differential DAC level over the span `-vref` to `+vref`. Drive `vop` and `von` complementarily around `V(vcm)`.

## Modeling Constraints
Use event-driven code sampling and smooth differential voltage outputs. Preserve the common mode, mid-rise half-LSB offset, and complementary polarity; do not invert the outputs or use the wrong code scale.

## Output Contract
Submit only the completed Verilog-A module in `ideal_dac_4bit_differential.va`.
