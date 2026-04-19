Write a voltage-domain Alexander-style bang-bang phase detector (BBPD) that captures
near-edge data/clock alignment behavior.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `data`, `up`, `dn`, `retimed_data`
2. Use event-driven edge handling with EVAS-compatible `cross()`
3. Emit bounded UP/DN pulses according to data-edge alignment around the clock
4. Keep UP and DN mostly non-overlapping
5. Use `transition()` for all driven outputs
6. Stay in pure electrical voltage domain
