Given a voltage-domain sample-and-hold DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that demonstrates clocked sampling and held
output behavior.

Requirements:

- provide `VDD`, `VSS`, a clock stimulus, and an analog input waveform
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `clk`: input electrical
- `in`: input electrical
- `out`: output electrical

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`

DUT module to instantiate: `sample_hold_step_ref`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=100n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `in`, `clk`, `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `clk`, `in`.
