Given a voltage-domain timer-based DCO DUT, generate a minimal EVAS-compatible
Spectre `.scs` testbench that applies a control-voltage step and saves the
control and clock waveforms.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `dco_gain_step_ref.va`
- Module name: `dco_gain_step_ref`
- Positional port order: `(VDD, VSS, vctrl, vout)`
- Required instance line:
  `XDUT (VDD VSS vctrl vout) dco_gain_step_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `vctrl` with a clear low-to-high or high-to-low step so the output
  frequency change is visible before and after the step.
- Use exactly one transient analysis:
  `tran tran stop=300n maxstep=100p`
- Save the public waveform columns:
  `save vctrl vout`
- Place the DUT include last:
  `ahdl_include "dco_gain_step_ref.va"`

## Public Evaluation Contract

The evaluator reads `vctrl` and `vout` from `tran.csv`. Use plain scalar save
names; do not rely on instance-qualified or aliased save names.
