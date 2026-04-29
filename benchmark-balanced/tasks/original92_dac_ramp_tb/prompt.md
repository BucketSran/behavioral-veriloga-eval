Given a voltage-domain DAC DUT, generate a minimal EVAS-compatible Spectre
`.scs` testbench that verifies a monotonic ramp response.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `dac_ramp_ref.va`
- Module name: `dac_ramp_ref`
- Positional port order: `(VDD, VSS, DIN3, DIN2, DIN1, DIN0, CLK, AOUT)`
- Required instance line:
  `XDUT (VDD VSS DIN3 DIN2 DIN1 DIN0 CLK AOUT) dac_ramp_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `CLK` with enough rising edges to sample a sequence of DAC codes.
- Drive `DIN3`, `DIN2`, `DIN1`, and `DIN0` as a 4-bit binary count over the
  transient window.
- Use exactly one transient analysis:
  `tran tran stop=68n maxstep=20p`
- Save the public waveform columns:
  `save CLK DIN3 DIN2 DIN1 DIN0 AOUT`
- Place the DUT include last:
  `ahdl_include "dac_ramp_ref.va"`

## Public Evaluation Contract

The evaluator reads `CLK`, `DIN3`, `DIN2`, `DIN1`, `DIN0`, and `AOUT` from
`tran.csv`. Use plain scalar save names; do not rely on instance-qualified or
aliased save names.
