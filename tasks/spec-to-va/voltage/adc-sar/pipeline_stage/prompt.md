Write a Verilog-A module named `pipeline_stage`.

Create a 1.5-bit pipeline ADC stage (MDAC) in Verilog-A. It should sample the input, compare against ±Vref/4 thresholds, compute the residue with gain-of-2, and output a 2-bit sub-ADC code.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `PHI1`: electrical
- `PHI2`: electrical
- `VIN`: electrical
- `VREF`: electrical
- `VRES`: electrical
- `D1`: electrical
- `D0`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `PHI1`: input electrical
- `PHI2`: input electrical
- `VIN`: input electrical
- `VREF`: input electrical
- `VRES`: output electrical
- `D1`: output electrical
- `D0`: output electrical
