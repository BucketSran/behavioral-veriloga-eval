# Two Period Sample Delay

## Task Contract
Implement the Verilog-A DUT `two_period_sample_delay.va` for an edge-updated sampled-data delay element.

## Public Verilog-A Interface
Provide `module two_period_sample_delay(update, ain, aout);` with electrical inputs `update`, `ain` and electrical output `aout`.

## Public Parameter Contract
Expose real parameters `vth = 0.5`, `tr = 50p`, and `init = 0.0`. Testbenches may override these parameters.

## Required Behavior
Initialize the internal samples and output to `init`. On each rising crossing of `update` through `vth`, output the previous sampled input value, then capture the current `ain` value for use on the next update. Hold `aout` between update events.

## Modeling Constraints
Use event-driven sampling with a retained previous sample and `transition` on the output. Do not implement a one-period delay, continuous tracking, half-gain output, or a testbench time table.

## Output Contract
Submit only the completed Verilog-A module in `two_period_sample_delay.va`.
