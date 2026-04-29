Given a 4-bit segmented DAC with two thermometer-style MSBs and two binary
LSBs, generate a minimal EVAS-compatible Spectre `.scs` testbench that scans
all codes, highlights boundary transitions, and saves the output waveform for
glitch and monotonicity inspection.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `segmented_dac_glitch_ref.va`
- Module name: `segmented_dac_glitch_ref`
- Positional port order: `(vdd, vss, clk, d3, d2, d1, d0, vout)`
- Required instance line:
  `XDUT (vdd vss clk d3 d2 d1 d0 vout) segmented_dac_glitch_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `vdd=0.9 V` and `vss=0 V`.
- Drive `clk` with enough rising edges to sample all DAC codes.
- Drive `d3`, `d2`, `d1`, and `d0` as a 4-bit binary count over the transient
  window.
- Include boundary transitions such as `3->4`, `7->8`, and `11->12`.
- Use exactly one transient analysis:
  `tran tran stop=160n maxstep=100p errpreset=conservative`
- Save the public waveform columns:
  `save clk d3 d2 d1 d0 vout`
- Place the DUT include last:
  `ahdl_include "segmented_dac_glitch_ref.va"`

## Public Evaluation Contract

The evaluator reads `clk`, `d3`, `d2`, `d1`, `d0`, and `vout` from `tran.csv`.
Use plain scalar save names; do not rely on instance-qualified or aliased save
names.
