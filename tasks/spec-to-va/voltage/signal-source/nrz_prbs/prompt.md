Write a Verilog-A NRZ data generator for SerDes testing.

Module name: `nrz_prbs`. PRBS-15 pattern, configurable data rate (default 10 Gbps), output amplitude, and pre-emphasis (1-tap FIR). Differential output.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `OUTP`: electrical
- `OUTN`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `OUTP`: output electrical
- `OUTN`: output electrical
