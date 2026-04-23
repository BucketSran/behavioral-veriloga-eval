Write a Verilog-A 10-bit SAR ADC logic block.

Module name: `sar_logic`.

Requirements:

- Inputs: `VDD`, `VSS`, `CLKS`, `DCOMP`
- Outputs: `DP_DAC[9:0]`, `RDY`
- Voltage-domain only
- Use clock-edge-driven SAR state sequencing
- Outputs must be driven with supply-referenced `transition()`
- No current contributions
- No testbench content

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `CLKS`: input electrical
- `DCOMP`: input electrical
- `DP_DAC_9`: output electrical
- `DP_DAC_8`: output electrical
- `DP_DAC_7`: output electrical
- `DP_DAC_6`: output electrical
- `DP_DAC_5`: output electrical
- `DP_DAC_4`: output electrical
- `DP_DAC_3`: output electrical
- `DP_DAC_2`: output electrical
- `DP_DAC_1`: output electrical
- `DP_DAC_0`: output electrical
- `RDY`: output electrical
