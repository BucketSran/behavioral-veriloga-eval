Given a voltage-domain XOR phase detector DUT, generate a minimal
EVAS-compatible Spectre-format `.scs` testbench that excites a fixed phase
offset between the reference and divided clocks.

Requirements:

- provide `VDD`, `VSS`, and two clock-like pulse sources with a non-zero phase offset
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `ref`: input electrical
- `div`: input electrical
- `pd_out`: output electrical

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`

DUT module to instantiate: `xor_phase_ref`
