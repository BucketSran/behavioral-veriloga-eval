Create an end-to-end Verilog-A evaluation case for the core function below.
Return the DUT Verilog-A model and a minimal Spectre/EVAS testbench.

Core function family: dac.
Balanced task-form completion derived from original task: `cdac_cal`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

Write a 10-bit capacitive DAC for a SAR ADC.

Module name: `cdac_cal`. Binary-weighted main array plus 2 redundant calibration capacitors. Differential topology (top-plate/bottom-plate). Model charge redistribution.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
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
- `CAL0`: electrical
- `CAL1`: electrical
- `VDAC_P`: electrical
- `VDAC_N`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
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
- `CAL0`: input electrical
- `CAL1`: input electrical
- `VDAC_P`: output electrical
- `VDAC_N`: output electrical

Implement this in Verilog-A behavioral modeling.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=68n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `CAL0`, `CAL1`, `VDAC_P`, `VDAC_N`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
