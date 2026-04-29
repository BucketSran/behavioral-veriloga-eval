Given a 4-bit segmented DAC with 2 thermometer-style MSBs and 2 binary LSBs,
write a minimal Spectre-compatible testbench that scans all codes, highlights
boundary transitions such as `3->4`, `7->8`, and `11->12`, and saves the output
waveform for glitch/monotonicity inspection.

Ports:
- `vdd`: inout electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `d3`: input electrical
- `d2`: input electrical
- `d1`: input electrical
- `d0`: input electrical
- `vout`: output electrical

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=160n maxstep=100p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `clk`, `d3`, `d2`, `d1`, `d0`, `vout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `d3`, `d2`, `d1`, `d0`.
