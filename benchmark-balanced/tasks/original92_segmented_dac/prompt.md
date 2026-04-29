Write a Verilog-A module named `segmented_dac`.

I need a 14-bit DAC with 6-bit thermometer MSBs and 8-bit binary LSBs. Differential current-steering output. Include INL/DNL-friendly unary decoding for the MSBs.

Ports:
- `VDD`: inout electrical power rail
- `VSS`: inout electrical power rail
- `CLK`: input electrical
- `D13`..`D0`: input electrical, with `D13` as the MSB and `D0` as the LSB
- `VOUT_P`: output electrical
- `VOUT_N`: output electrical

Use this exact module port order:

```verilog
module segmented_dac(VDD, VSS, CLK, D13, D12, D11, D10, D9, D8, D7, D6, D5, D4, D3, D2, D1, D0, VOUT_P, VOUT_N);
```

Verilog-A compatibility requirements:

- Use Spectre-compatible Verilog-A syntax for scalar integer arithmetic and
  data-bit decoding.
- Use pure voltage-domain contributions only: drive outputs with `V(node) <+`
  and do not use current contributions.
- Return the Verilog-A module code only.


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
