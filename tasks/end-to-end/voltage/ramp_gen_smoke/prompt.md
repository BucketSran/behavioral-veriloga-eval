Write a Verilog-A module named `ramp_gen`.

Create a voltage-domain ramp generator in Verilog-A, then produce a minimal EVAS
testbench and run a smoke simulation.

Behavioral intent:

- resettable ramp code generator
- synchronous to a digital clock
- monotonic increasing code
- output as a 4-bit digital bus

Ports:
- `clk_in`: input electrical
- `rst_n`: input electrical
- `code_3`: output electrical
- `code_2`: output electrical
- `code_1`: output electrical
- `code_0`: output electrical
