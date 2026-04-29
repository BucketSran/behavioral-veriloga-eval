Given a voltage-domain NRZ PRBS source DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that can expose jittered bit transitions and burst gaps.

Requirements:

1. Provide `VDD`, `VSS`, and a clock source
2. Include an `enable` stimulus with at least one on/off burst window
3. Instantiate the DUT by position
4. Include `tran`
5. Include explicit `save` for `clk`, `enable`, `sout_p`, `sout_n`
6. Place `ahdl_include` last

Ports:
- `vdd`: inout electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `enable`: input electrical
- `sout_p`: output electrical
- `sout_n`: output electrical

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=95n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `clk`, `enable`, `sout_p`, `sout_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Enable-like input(s) `enable` must be in the enabled state during the post-reset checking window unless the task explicitly asks for disabled intervals.
- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `enable`.
