Given a voltage-domain clock divider DUT, generate a minimal EVAS-compatible
Spectre `.scs` testbench.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `clk_div_min.va`
- Module name: `clk_div_min`
- Positional port order: `(VDD, VSS, CLK, RST_N, CLK_OUT)`
- Required instance line:
  `XDUT (VDD VSS CLK RST_N CLK_OUT) clk_div_min`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `CLK` with enough rising edges for divider output observation.
- Drive active-low `RST_N` low at startup, then release it high early enough
  for post-reset checking.
- Use exactly one transient analysis:
  `tran tran stop=24n maxstep=20p`
- Save the public waveform columns:
  `save CLK RST_N CLK_OUT`
- Place the DUT include last:
  `ahdl_include "clk_div_min.va"`

## Public Evaluation Contract

The evaluator reads `CLK`, `RST_N`, and `CLK_OUT` from `tran.csv`. Use plain
scalar save names; do not rely on instance-qualified or aliased save names.
