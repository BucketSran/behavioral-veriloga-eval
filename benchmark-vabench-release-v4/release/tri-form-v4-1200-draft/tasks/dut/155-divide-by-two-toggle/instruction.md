# Divide By Two Toggle

## Task Contract
Implement the Verilog-A DUT `divide_by_two_toggle.va` for a legacy voltage-domain divide-by-two toggle row.

## Public Verilog-A Interface
Provide `module divide_by_two_toggle(clkin, clkout);` with electrical input `clkin` and electrical output `clkout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Initialize the internal state low. On each rising crossing of `clkin` through 0.5 V, toggle the internal state. Drive `clkout` to 0.9 V when the state is high and 0.0 V when it is low.

## Modeling Constraints
Use event-driven retained state and `transition` for the output. Do not set high only once, start in the wrong state, use half high level, or derive the output from absolute time.

## Output Contract
Submit only the completed Verilog-A module in `divide_by_two_toggle.va`.
