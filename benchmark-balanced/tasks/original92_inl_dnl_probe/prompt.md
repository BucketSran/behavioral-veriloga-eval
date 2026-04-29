Generate a minimal EVAS-compatible Spectre `.scs` testbench for an INL/DNL
probe smoke run.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the following Verilog-A files are provided by the benchmark harness and only
write the Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided Modules

1. DAC stimulus target:
   - Include file: `dac_for_probe.va`
   - Module name: `dac_for_probe`
   - Positional port order: `(VDD, VSS, DIN3, DIN2, DIN1, DIN0, CLK, AOUT)`

2. INL/DNL probe:
   - Include file: `inl_dnl_probe.va`
   - Module name: `inl_dnl_probe`
   - Positional port order: `(VDD, VSS, CLKSTB, VOUT)`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `CLK` with enough rising edges to sample all 16 DAC codes.
- Drive `DIN3`, `DIN2`, `DIN1`, and `DIN0` as a 4-bit binary count over the
  transient window.
- Instantiate the DAC by position:
  `XDAC (VDD VSS DIN3 DIN2 DIN1 DIN0 CLK AOUT) dac_for_probe`
- Instantiate the probe by position:
  `XPROBE (VDD VSS CLK AOUT) inl_dnl_probe`
- Use exactly one transient analysis:
  `tran tran stop=68n maxstep=20p`
- Save the public waveform columns:
  `save CLK DIN3 DIN2 DIN1 DIN0 AOUT`
- Place the `ahdl_include` lines last:
  `ahdl_include "dac_for_probe.va"`
  `ahdl_include "inl_dnl_probe.va"`

## Public Evaluation Contract

The evaluator reads the transient waveform columns `CLK`, `DIN3`, `DIN2`,
`DIN1`, `DIN0`, and `AOUT`. Use plain scalar save names; do not rely on
instance-qualified or aliased save names.
