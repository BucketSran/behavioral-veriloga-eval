Write a pure voltage-domain Verilog-A sample-and-hold with observable hold droop.

Module name: `sample_hold_droop_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `vin`, `vout`
2. Sample on rising `clk` edge
3. Output should hold sampled value between edges
4. Add finite droop during hold windows (e.g., leakage-like decay toward `vss`)
5. Use EVAS-compatible `cross()` and `transition()` style
6. Keep implementation fully in electrical voltage domain

Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `vin`: electrical
- `vout`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `vin`: input electrical
- `vout`: output electrical
