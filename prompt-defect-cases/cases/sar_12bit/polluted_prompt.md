Write a 12-bit SAR ADC logic block with differential input, comparator interface, and CDAC control outputs.

Module name: `sar_12bit`. Include end-of-conversion flag.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `CLKS`: input electrical
- `DCOMP_P`: input electrical
- `DCOMP_N`: input electrical
- `DP_CAP_11`: output electrical
- `DP_CAP_10`: output electrical
- `DP_CAP_9`: output electrical
- `DP_CAP_8`: output electrical
- `DP_CAP_7`: output electrical
- `DP_CAP_6`: output electrical
- `DP_CAP_5`: output electrical
- `DP_CAP_4`: output electrical
- `DP_CAP_3`: output electrical
- `DP_CAP_2`: output electrical
- `DP_CAP_1`: output electrical
- `DP_CAP_0`: output electrical
- `EOC`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=6u maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `eoc`, `dp_cap_11`, `dp_cap_0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
