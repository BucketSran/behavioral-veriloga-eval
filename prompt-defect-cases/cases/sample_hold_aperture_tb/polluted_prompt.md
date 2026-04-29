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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=140n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `vin`, `clk`, `vout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `clk`, `vin`.
