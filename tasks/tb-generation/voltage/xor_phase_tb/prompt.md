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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `ref`, `div`, `pd_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `ref`, `div`.
