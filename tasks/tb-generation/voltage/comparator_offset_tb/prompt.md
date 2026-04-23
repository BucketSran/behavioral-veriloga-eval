Given a voltage-domain comparator DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench to measure comparator offset behavior.

Requirements:

- provide `VDD`, `VSS`, and a clock if needed
- drive the differential input with a small sweep or stepped offset
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `VINP`: input electrical
- `VINN`: input electrical
- `OUT_P`: output electrical

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`

DUT module to instantiate: `cmp_offset_ref`
