Create a testbench probe that monitors a DAC output and computes code-by-code INL and DNL. Input: analog DAC output + clock strobe. Output: writes results to a file using $fopen/$fdisplay at end of simulation.

Ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `DIN3`: input electrical
- `DIN2`: input electrical
- `DIN1`: input electrical
- `DIN0`: input electrical
- `CLK`: input electrical
- `AOUT`: output electrical

DUT module to instantiate: `dac_for_probe`

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=68n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `DIN3`, `DIN2`, `DIN1`, `DIN0`, `AOUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `CLK`, `DIN0`, `DIN1`, `DIN2`, `DIN3`.
