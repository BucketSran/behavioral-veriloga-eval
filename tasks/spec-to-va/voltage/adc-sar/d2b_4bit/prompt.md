Write a 4-bit static analog-to-binary converter module named _va_d2b_4b.

Module name: `_va_d2b_4b`. Input: analog voltage VIN (range VSS to VDD). Output: 4-bit binary code DOUT[3:0]. No clock — purely combinational, continuous tracking. Use VDD/VSS power ports.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VIN`: input electrical
- `DOUT3`: output electrical
- `DOUT2`: output electrical
- `DOUT1`: output electrical
- `DOUT0`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=110n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `vin`, `DOUT3`, `DOUT2`, `DOUT1`, `DOUT0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
