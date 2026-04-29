Given a voltage-domain timer-based DCO DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that applies a control-voltage step and saves
the control and clock waveforms so frequency change can be measured before and
after the step.

Requirements:

- provide `VDD`, `VSS`, and a `vctrl` stimulus
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vctrl`: input electrical
- `vout`: output electrical

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=300n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `vctrl`, `vout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `vctrl`.
