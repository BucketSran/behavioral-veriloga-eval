Given a voltage-domain comparator DUT, generate a minimal EVAS-compatible
Spectre `.scs` testbench to expose comparator offset behavior.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `cmp_offset_ref.va`
- Module name: `cmp_offset_ref`
- Positional port order: `(VDD, VSS, CLK, VINP, VINN, OUT_P)`
- Required instance line:
  `XDUT (VDD VSS CLK VINP VINN OUT_P) cmp_offset_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `CLK` with repeated rising edges.
- Drive `VINP` and `VINN` with a small differential sweep or stepped offset so
  the output transition region can be observed.
- Use exactly one transient analysis:
  `tran tran stop=28n maxstep=20p`
- Save the public waveform columns:
  `save CLK VINP VINN OUT_P`
- Place the DUT include last:
  `ahdl_include "cmp_offset_ref.va"`

## Public Evaluation Contract

The evaluator reads `CLK`, `VINP`, `VINN`, and `OUT_P` from `tran.csv`. Use
plain scalar save names; do not rely on instance-qualified or aliased save
names.
