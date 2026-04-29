Given a voltage-domain NRZ PRBS source DUT, generate a minimal EVAS-compatible
Spectre `.scs` testbench that exposes jittered bit transitions and burst gaps.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `nrz_prbs_jitter_ref.va`
- Module name: `nrz_prbs_jitter_ref`
- Positional port order: `(vdd, vss, clk, enable, sout_p, sout_n)`
- Required instance line:
  `XDUT (vdd vss clk enable sout_p sout_n) nrz_prbs_jitter_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `vdd=0.9 V` and `vss=0 V`.
- Drive `clk` with enough edges for multiple output transitions.
- Drive `enable` with at least one enabled burst and one disabled gap.
- Use exactly one transient analysis:
  `tran tran stop=95n maxstep=20p`
- Save the public waveform columns:
  `save clk enable sout_p sout_n`
- Place the DUT include last:
  `ahdl_include "nrz_prbs_jitter_ref.va"`

## Public Evaluation Contract

The evaluator reads `clk`, `enable`, `sout_p`, and `sout_n` from `tran.csv`.
Use plain scalar save names; do not rely on instance-qualified or aliased save
names.
