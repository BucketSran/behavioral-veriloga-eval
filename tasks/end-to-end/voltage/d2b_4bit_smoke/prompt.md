Write a Verilog-A module named `d2b_4bit`.

Create a 4-bit static analog-to-binary converter in Verilog-A, then produce a
minimal EVAS testbench and run a smoke simulation.

Behavioral intent:

- continuous tracking, no clock
- analog input over the VSS-to-VDD range
- 4-bit digital output bus
- output code should increase as input voltage increases

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VIN`: input electrical
- `DOUT3`: output electrical
- `DOUT2`: output electrical
- `DOUT1`: output electrical
- `DOUT0`: output electrical
