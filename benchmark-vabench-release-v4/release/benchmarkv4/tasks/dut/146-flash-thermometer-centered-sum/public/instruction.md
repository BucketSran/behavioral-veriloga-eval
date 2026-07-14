# Flash Thermometer Centered Sum

## Task Contract
Implement the Verilog-A DUT `flash_thermometer_centered_sum.va` for an eight-input voltage-coded flash thermometer summarizer.

## Public Verilog-A Interface
Provide `module flash_thermometer_centered_sum(b0, b1, b2, b3, b4, b5, b6, b7, dout);` with electrical inputs `b0` through `b7` and electrical output `dout`.

## Public Parameter Contract
Expose real parameters `vth = 0.45` and `gain = 0.1125`. Testbenches may override these parameters.

## Required Behavior
Count how many thermometer inputs are above `vth`. Center the count around midscale by subtracting four asserted inputs, then scale the centered count by `gain` and drive `dout`.

## Modeling Constraints
Use voltage-coded threshold decisions and a continuous analog output. Do not output an uncentered sum, use the wrong gain, or ignore upper thermometer inputs.

## Output Contract
Submit only the completed Verilog-A module in `flash_thermometer_centered_sum.va`.
