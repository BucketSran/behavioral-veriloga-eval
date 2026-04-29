Given a voltage-domain sample-and-hold DUT, generate a minimal
EVAS-compatible Spectre-format `.scs` testbench that demonstrates clocked
sampling and held output behavior.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `sample_hold_step_ref.va`
- Module name: `sample_hold_step_ref`
- Positional port order: `(VDD, VSS, clk, in, out)`
- Required instance line:
  `XDUT (VDD VSS clk in out) sample_hold_step_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `clk` with repeated rising edges throughout the run.
- Drive `in` with a stepped analog waveform so the held output can be checked
  after clock edges.
- Use exactly one transient analysis:
  `tran tran stop=100n maxstep=100p`
- Save the public waveform columns:
  `save in clk out`
- Place the DUT include last:
  `ahdl_include "sample_hold_step_ref.va"`

## Public Evaluation Contract

The evaluator reads the transient waveform columns `in`, `clk`, and `out`.
Use plain scalar save names; do not rely on instance-qualified or aliased save
names.
