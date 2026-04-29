Write a Verilog-A 10-bit SAR ADC logic block.

Module name: `sar_logic`. It should take a comparator output (DCOMP) and a sample clock (CLKS), and generate 10 DAC control bits (DP_DAC[9:0]) plus a ready flag (RDY). Use rising edge of an internal bit-clock derived from CLKS. Include VDD and VSS as power ports.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `CLKS`: input electrical
- `DCOMP`: input electrical
- `DP_DAC_9`: output electrical
- `DP_DAC_8`: output electrical
- `DP_DAC_7`: output electrical
- `DP_DAC_6`: output electrical
- `DP_DAC_5`: output electrical
- `DP_DAC_4`: output electrical
- `DP_DAC_3`: output electrical
- `DP_DAC_2`: output electrical
- `DP_DAC_1`: output electrical
- `DP_DAC_0`: output electrical
- `RDY`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=5u maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `rdy`, `dp_dac_9`, `dp_dac_0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
