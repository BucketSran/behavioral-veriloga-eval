Given a voltage-domain XOR phase detector DUT, generate a minimal
EVAS-compatible Spectre `.scs` testbench that excites a fixed phase offset
between the reference and divided clocks.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `xor_phase_ref.va`
- Module name: `xor_phase_ref`
- Positional port order: `(VDD, VSS, ref, div, pd_out)`
- Required instance line:
  `XDUT (VDD VSS ref div pd_out) xor_phase_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `ref` and `div` as clock-like pulse sources with a nonzero phase
  offset.
- Use exactly one transient analysis:
  `tran tran stop=80n maxstep=50p`
- Save the public waveform columns:
  `save ref div pd_out`
- Place the DUT include last:
  `ahdl_include "xor_phase_ref.va"`

## Public Evaluation Contract

The evaluator reads `ref`, `div`, and `pd_out` from `tran.csv`. Use plain
scalar save names; do not rely on instance-qualified or aliased save names.
