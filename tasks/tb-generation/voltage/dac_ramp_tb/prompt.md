Given a voltage-domain DAC DUT, generate a minimal EVAS-compatible Spectre-format
`.scs` testbench that verifies a monotonic ramp response.

Requirements:

- provide `VDD` and `VSS`
- create a simple code stimulus that steps through several DAC codes
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `DIN3`: input electrical
- `DIN2`: input electrical
- `DIN1`: input electrical
- `DIN0`: input electrical
- `CLK`: input electrical
- `AOUT`: output electrical

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`

DUT module to instantiate: `dac_ramp_ref`
