# Divide By Eight Clock

## Task Contract
Implement the Verilog-A DUT `divide_by_eight_clock.va` for a resettable, enable-qualified voltage-domain clock divider.

## Public Verilog-A Interface
Provide `module divide_by_eight_clock(vin, rst, en, vout);` with electrical inputs `vin`, `rst`, `en` and electrical output `vout`.

## Public Parameter Contract
Expose integer `divisor = 8` and real parameters `tdel = 10p`, `tr = 20p`, `tf = 20p`, `vdd = 0.9`, and `vth = 0.45`. Testbenches may override these parameters.

## Required Behavior
Initialize the divided output high. An active-high reset forces the counter to zero and the output high. On rising input-clock crossings through `vth`, advance the counter only when reset is low and enable is high. Wrap the counter modulo `divisor` and drive the output high for the first half of the count range and low for the second half.

## Modeling Constraints
Use event-driven state updates and `transition` for the output. Do not ignore reset or enable, use divide-by-four behavior, or change the output duty rule.

## Output Contract
Submit only the completed Verilog-A module in `divide_by_eight_clock.va`.
