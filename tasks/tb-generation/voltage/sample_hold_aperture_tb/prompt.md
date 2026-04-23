Given a voltage-domain sample-and-hold DUT with a nonzero aperture offset,
generate a minimal EVAS-compatible Spectre-format `.scs` testbench that drives
clocked sampling against a changing analog input and saves the waveforms needed
to inspect capture timing.

Requirements:

- provide `VDD`, `VSS`, a clock stimulus, and an analog input waveform
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `clk`: input electrical
- `vin`: input electrical
- `vout`: output electrical

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`

DUT module to instantiate: `sample_hold_aperture_ref`
