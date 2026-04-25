Write a programmable clock divider.

Module name: `clk_divider_ref`. 8-bit division ratio (1-255). 50% output duty cycle regardless of division ratio. Synchronous reset. Include a LOCK output that goes high after the first full output period.

Ports:
- `clk_in`: input electrical
- `rst_n`: input electrical
- `div_code_0`: input electrical
- `div_code_1`: input electrical
- `div_code_2`: input electrical
- `div_code_3`: input electrical
- `div_code_4`: input electrical
- `div_code_5`: input electrical
- `div_code_6`: input electrical
- `div_code_7`: input electrical
- `clk_out`: output electrical
- `lock`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `clk_in`, `clk_out`, `lock`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
