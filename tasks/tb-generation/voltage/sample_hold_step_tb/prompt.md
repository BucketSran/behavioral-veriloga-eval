Given a voltage-domain sample-and-hold DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that demonstrates clocked sampling and held
output behavior.

Requirements:

- provide `VDD`, `VSS`, a clock stimulus, and an analog input waveform
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last
