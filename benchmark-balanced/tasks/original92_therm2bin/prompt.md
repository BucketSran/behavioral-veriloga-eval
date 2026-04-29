Write a Verilog-A thermometer-to-binary encoder.

Module name: `therm2bin_ref`. 15-bit thermometer input, 4-bit binary output. Handle bubble errors (non-monotonic thermometer codes) gracefully.

Ports:
- `therm_0`: input electrical
- `therm_1`: input electrical
- `therm_2`: input electrical
- `therm_3`: input electrical
- `therm_4`: input electrical
- `therm_5`: input electrical
- `therm_6`: input electrical
- `therm_7`: input electrical
- `therm_8`: input electrical
- `therm_9`: input electrical
- `therm_10`: input electrical
- `therm_11`: input electrical
- `therm_12`: input electrical
- `therm_13`: input electrical
- `therm_14`: input electrical
- `bin_0`: output electrical
- `bin_1`: output electrical
- `bin_2`: output electrical
- `bin_3`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=18n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `therm_0`, `therm_1`, `therm_2`, `therm_3`, `therm_4`, `therm_5`, `therm_6`, `therm_7`
- `therm_8`, `therm_9`, `therm_10`, `therm_11`, `therm_12`, `therm_13`, `therm_14`, `bin_0`
- `bin_1`, `bin_2`, `bin_3`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
