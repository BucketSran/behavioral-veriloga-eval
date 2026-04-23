Write a Verilog-A module named `comparator`.

Create a voltage-domain comparator in Verilog-A, then produce a minimal EVAS
testbench and run a smoke simulation.

Behavioral intent:

- differential comparison
- output toggles high/low with supply-referenced logic levels
- finite output edge transition
- threshold crossing should be visible in the waveform

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VINP`: input electrical
- `VINN`: input electrical
- `OUT_P`: output electrical
