Given a voltage-domain differential gain-stage DUT, generate a minimal
EVAS-compatible Spectre-format `.scs` testbench that applies a small
differential input step and saves both input and output waveforms.

Requirements:

- provide `VDD`, `VSS`, and differential input sources
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `vinp`: input electrical
- `vinn`: input electrical
- `voutp`: output electrical
- `voutn`: output electrical

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`

DUT module to instantiate: `gain_step_ref`
