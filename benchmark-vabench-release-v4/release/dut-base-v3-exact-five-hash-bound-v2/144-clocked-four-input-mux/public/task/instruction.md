# Clocked Four Input Mux

## Task Contract
Implement the Verilog-A DUT `clocked_four_input_mux.va` for a falling-edge sampled 4:1 analog mux.

## Public Verilog-A Interface
Provide `module clocked_four_input_mux(dsel0, dsel1, din0, din1, din2, din3, clks, dout);` with electrical select inputs `dsel0`, `dsel1`, electrical data inputs `din0` through `din3`, clock input `clks`, and electrical output `dout`.

## Public Parameter Contract
Expose real parameters `vth = 0.45` and `tr = 20p`. Testbenches may override these parameters.

## Required Behavior
On each falling crossing of `clks` through `vth`, decode `dsel0` as the LSB and `dsel1` as the MSB using threshold `vth`, sample the selected data input, and hold that sampled value on `dout` until the next clock event.

## Modeling Constraints
Use an event-updated internal register and `transition` for `dout`. Do not continuously track select changes between clock edges, swap select-bit weights, ignore `dsel1`, or latch on the wrong edge.

## Output Contract
Submit only the completed Verilog-A module in `clocked_four_input_mux.va`.
