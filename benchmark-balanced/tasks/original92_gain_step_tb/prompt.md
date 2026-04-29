Given a voltage-domain differential gain-stage DUT, generate a minimal
EVAS-compatible Spectre `.scs` testbench that applies a small differential
input step and saves both input and output waveforms.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `gain_step_ref.va`
- Module name: `gain_step_ref`
- Positional port order: `(VDD, VSS, vinp, vinn, voutp, voutn)`
- Required instance line:
  `XDUT (VDD VSS vinp vinn voutp voutn) gain_step_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `vinp` and `vinn` with a small differential input step.
- Use exactly one transient analysis:
  `tran tran stop=100n maxstep=100p`
- Save the public waveform columns:
  `save vinp vinn voutp voutn`
- Place the DUT include last:
  `ahdl_include "gain_step_ref.va"`

## Public Evaluation Contract

The evaluator reads `vinp`, `vinn`, `voutp`, and `voutn` from `tran.csv`. Use
plain scalar save names; do not rely on instance-qualified or aliased save
names.
