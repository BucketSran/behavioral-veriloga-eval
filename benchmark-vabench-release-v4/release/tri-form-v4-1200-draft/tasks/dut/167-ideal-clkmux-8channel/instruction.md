# Ideal Clock Mux 8channel

## Task Contract
Implement the Verilog-A DUT `ideal_clkmux_8channel.va` for an eight-channel analog input mux driven by an internal modulo counter.

## Public Verilog-A Interface
Provide `module ideal_clkmux_8channel(clk, in0, in1, in2, in3, in4, in5, in6, in7, out, count_x);` with electrical clock input `clk`, electrical inputs `in0` through `in7`, and electrical outputs `out`, `count_x`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Initialize an internal modulo-8 counter to zero. On each rising crossing of `clk` through 0.5 V, increment the counter modulo eight. Route the input selected by the current counter value to `out`, and drive `count_x` with the current counter value as an analog voltage.

## Modeling Constraints
Use event-driven counter state and analog mux selection. Do not use modulo seven, omit the initial increment behavior, halve the count output, or route a fixed channel sequence by time.

## Output Contract
Submit only the completed Verilog-A module in `ideal_clkmux_8channel.va`.
