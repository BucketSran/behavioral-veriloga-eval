Write a background calibration module that measures comparator offset via a chopping technique.

Module name: `bg_cal`. Inputs: COMP_OUT, CLK. Output: 6-bit trim code (TRIM[5:0]). It should average N comparisons, compute the offset direction, and adjust the trim code by ±1 LSB each calibration cycle. Include a SETTLED output flag when trim code stops changing for 8 consecutive cycles.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `COMP_OUT`: electrical
- `SETTLED`: electrical
- `TRIM_0`: electrical
- `TRIM_1`: electrical
- `TRIM_2`: electrical
- `TRIM_3`: electrical
- `TRIM_4`: electrical
- `TRIM_5`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `COMP_OUT`: input electrical
- `SETTLED`: output electrical
- `TRIM_0`: output electrical
- `TRIM_1`: output electrical
- `TRIM_2`: output electrical
- `TRIM_3`: output electrical
- `TRIM_4`: output electrical
- `TRIM_5`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=700n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `COMP_OUT`, `SETTLED`, `TRIM_0`, `TRIM_1`, `TRIM_2`, `TRIM_3`, `TRIM_4`
- `TRIM_5`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
