Write a Verilog-A module named `segmented_dac`.

I need a 14-bit DAC with 6-bit thermometer MSBs and 8-bit binary LSBs. Differential current-steering output. Include INL/DNL-friendly unary decoding for the MSBs.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `D13`: electrical
- `D12`: electrical
- `D11`: electrical
- `D10`: electrical
- `D9`: electrical
- `D8`: electrical
- `D7`: electrical
- `D6`: electrical
- `D5`: electrical
- `D4`: electrical
- `D3`: electrical
- `D2`: electrical
- `D1`: electrical
- `D0`: electrical
- `VOUT_P`: electrical
- `VOUT_N`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `D13`: input electrical
- `D12`: input electrical
- `D11`: input electrical
- `D10`: input electrical
- `D9`: input electrical
- `D8`: input electrical
- `D7`: input electrical
- `D6`: input electrical
- `D5`: input electrical
- `D4`: input electrical
- `D3`: input electrical
- `D2`: input electrical
- `D1`: input electrical
- `D0`: input electrical
- `VOUT_P`: output electrical
- `VOUT_N`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=68n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `D8`, `D3`, `D2`, `D1`, `D0`, `VOUT_P`, `VOUT_N`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
