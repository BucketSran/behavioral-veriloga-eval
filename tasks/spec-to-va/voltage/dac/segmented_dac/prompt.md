Write a Verilog-A module named `segmented_dac`.

I need a 14-bit DAC with 6-bit thermometer MSBs and 8-bit binary LSBs. Differential current-steering output. Include INL/DNL-friendly unary decoding for the MSBs.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `D13`: electrical
- `D12`: electrical
- `D11`: electrical
- `D10`: electrical
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
- `VOUT_P`: electrical
- `VOUT_N`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `D13`: input electrical
- `D12`: input electrical
- `D11`: input electrical
- `D10`: input electrical
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
- `VOUT_P`: output electrical
- `VOUT_N`: output electrical
