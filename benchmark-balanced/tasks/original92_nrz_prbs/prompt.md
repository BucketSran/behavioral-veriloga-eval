Write a Verilog-A NRZ data generator for SerDes testing.

Module name: `nrz_prbs`. PRBS-15 pattern, configurable data rate (default 10 Gbps), output amplitude, and pre-emphasis (1-tap FIR). Differential output.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `OUTP`: electrical
- `OUTN`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `OUTP`: output electrical
- `OUTN`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=12n maxstep=10p
```

Required public waveform columns in `tran.csv`:

- `OUTP`, `OUTN`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
