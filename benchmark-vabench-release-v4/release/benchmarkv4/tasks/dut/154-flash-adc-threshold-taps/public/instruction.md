# Flash ADC Threshold Taps

## Task Contract
Implement the Verilog-A DUT `flash_adc_threshold_taps.va` for a clocked selected-tap flash ADC thermometer output.

## Public Verilog-A Interface
Provide `module flash_adc_threshold_taps(vin, clk, dout0, dout1, dout2, dout3, dout4, dout5, dout6);` with electrical inputs `vin`, `clk` and electrical outputs `dout0` through `dout6`.

## Public Parameter Contract
Expose real parameters `vrefp = 0.125`, `vrefn = -0.125`, `vl = 0.0`, `vh = 0.9`, and `vth = 0.45`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clk` through `vth`, compare `vin` against seven selected thresholds at tap indices 1, 5, 10, 15, 20, 25, and 30 of a 31-step span from `vrefn` to `vrefp`. Drive each `dout` high at `vh` when `vin` exceeds its tap threshold and low at `vl` otherwise.

## Modeling Constraints
Use clocked sampling and voltage-coded thermometer outputs. Do not omit the top tap, invert the outputs, use half high level, or continuously update the outputs without a clock event.

## Output Contract
Submit only the completed Verilog-A module in `flash_adc_threshold_taps.va`.
