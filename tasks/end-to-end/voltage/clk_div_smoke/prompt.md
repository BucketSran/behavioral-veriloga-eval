Write a Verilog-A module named `clk_div`.

Create a voltage-domain clock divider in Verilog-A, then produce a minimal EVAS
testbench and run a smoke simulation.

Behavioral intent:

- input clock and synchronous reset
- divide-by-4 output
- 50% duty-cycle style output if practical
- one digital output clock node

Ports:
- `CLK_IN`: input electrical
- `RST_N`: input electrical
- `CLK_OUT`: output electrical
