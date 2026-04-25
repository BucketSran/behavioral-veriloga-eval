Write a Verilog-A module named `multimod_divider_ref`.

Create a Verilog-A multi-modulus divider that can divide by N or N+1, controlled by a MOD input. Include prescaler output and a 4-bit modulus control word.

Ports:
- `clk_in`: input electrical
- `mod`: input electrical
- `mod_0`: input electrical
- `mod_1`: input electrical
- `mod_2`: input electrical
- `mod_3`: input electrical
- `prescaler_out`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=90n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `clk_in`, `mod`, `prescaler_out`, `mod_0`, `mod_1`, `mod_2`, `mod_3`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
