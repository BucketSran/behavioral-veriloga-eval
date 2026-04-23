Write a background calibration module that measures comparator offset via a chopping technique.

Module name: `bg_cal`. Inputs: COMP_OUT, CLK. Output: 6-bit trim code (TRIM[5:0]). It should average N comparisons, compute the offset direction, and adjust the trim code by ±1 LSB each calibration cycle. Include a SETTLED output flag when trim code stops changing for 8 consecutive cycles.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `COMP_OUT`: electrical
- `SETTLED`: electrical
- `TRIM_0`: electrical
- `TRIM_1`: electrical
- `TRIM_2`: electrical
- `TRIM_3`: electrical
- `TRIM_4`: electrical
- `TRIM_5`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `COMP_OUT`: input electrical
- `SETTLED`: output electrical
- `TRIM_0`: output electrical
- `TRIM_1`: output electrical
- `TRIM_2`: output electrical
- `TRIM_3`: output electrical
- `TRIM_4`: output electrical
- `TRIM_5`: output electrical

Implement this in Verilog-A behavioral modeling.
