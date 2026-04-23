Write a voltage-domain Alexander-style bang-bang phase detector (BBPD) that captures
near-edge data/clock alignment behavior.

Module name: `bbpd_data_edge_alignment_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `data`, `up`, `dn`, `retimed_data`
2. Use event-driven edge handling with EVAS-compatible `cross()`
3. Emit bounded UP/DN pulses according to data-edge alignment around the clock
4. Keep UP and DN mostly non-overlapping
5.  Stay in pure electrical voltage domain

Expected behavior:
- up pulse should fire when data edge leads clock edge
- dn pulse should fire when data edge lags clock edge
- up and dn should NOT overlap (overlap_frac < 2%)
- At least 6 data edges should generate up/dn pulses
Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `data`: electrical
- `up`: electrical
- `dn`: electrical
- `retimed_data`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `data`: input electrical
- `up`: output electrical
- `dn`: output electrical
- `retimed_data`: output electrical

Implement this in Verilog-A behavioral modeling.
