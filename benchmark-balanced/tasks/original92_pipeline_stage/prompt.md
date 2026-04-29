Write a Verilog-A module named `pipeline_stage`.

Create a 1.5-bit pipeline ADC stage (MDAC) in Verilog-A. It should sample the input, compare against ±Vref/4 thresholds, compute the residue with gain-of-2, and output a 2-bit sub-ADC code.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `PHI1`: electrical
- `PHI2`: electrical
- `VIN`: electrical
- `VREF`: electrical
- `VRES`: electrical
- `D1`: electrical
- `D0`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `PHI1`: input electrical
- `PHI2`: input electrical
- `VIN`: input electrical
- `VREF`: input electrical
- `VRES`: output electrical
- `D1`: output electrical
- `D0`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=300n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `phi1`, `phi2`, `vin`, `vres`, `d1`, `d0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
