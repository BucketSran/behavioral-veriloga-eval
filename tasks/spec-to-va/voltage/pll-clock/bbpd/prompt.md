Write a bang-bang (binary) phase-frequency detector for a CDR.

Module name: `bbpd_ref`. Three inputs: DATA, CLK, and RETIMED_DATA. Outputs: UP and DOWN pulses. Edge-triggered on DATA transitions.

Ports:
- `data`: input electrical
- `clk`: input electrical
- `retimed_data`: input electrical
- `up`: output electrical
- `down`: output electrical

Implement this in Verilog-A behavioral modeling.
