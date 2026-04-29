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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=28n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `VINP`, `VINN`, `OUT_P`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `CLK`, `VINP`, `VINN`.
