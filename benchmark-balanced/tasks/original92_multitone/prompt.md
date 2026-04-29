Write a Verilog-A module named `multitone`.

Create a signal source that outputs the sum of N sinusoids. Parameters: an array of frequencies and amplitudes (up to 8 tones). Include $bound_step for the highest frequency component.

Ports:
- `OUT`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=500n maxstep=500p
```

Required public waveform columns in `tran.csv`:

- `OUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
