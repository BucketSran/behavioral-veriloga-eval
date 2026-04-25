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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=100n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `vinp`, `vinn`, `voutp`, `voutn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `vinp`, `vinn`.
