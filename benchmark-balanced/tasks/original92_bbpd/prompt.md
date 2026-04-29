Write a bang-bang (binary) phase-frequency detector for a CDR.

Module name: `bbpd_ref`. Three inputs: DATA, CLK, and RETIMED_DATA. Outputs: UP and DOWN pulses. Edge-triggered on DATA transitions.

Ports:
- `data`: input electrical
- `clk`: input electrical
- `retimed_data`: input electrical
- `up`: output electrical
- `down`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=60n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `data`, `clk`, `retimed_data`, `up`, `down`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
