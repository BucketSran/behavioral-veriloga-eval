Write a 10-bit capacitive DAC for a SAR ADC.

Module name: `cdac_cal`. Binary-weighted main array plus 2 redundant calibration capacitors. Differential topology (top-plate/bottom-plate). Model charge redistribution.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `D9`: electrical
- `D8`: electrical
- `D7`: electrical
- `D6`: electrical
- `D5`: electrical
- `D4`: electrical
- `D3`: electrical
- `D2`: electrical
- `D1`: electrical
- `D0`: electrical
- `CAL0`: electrical
- `CAL1`: electrical
- `VDAC_P`: electrical
- `VDAC_N`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `D9`: input electrical
- `D8`: input electrical
- `D7`: input electrical
- `D6`: input electrical
- `D5`: input electrical
- `D4`: input electrical
- `D3`: input electrical
- `D2`: input electrical
- `D1`: input electrical
- `D0`: input electrical
- `CAL0`: input electrical
- `CAL1`: input electrical
- `VDAC_P`: output electrical
- `VDAC_N`: output electrical

Implement this in Verilog-A behavioral modeling.
