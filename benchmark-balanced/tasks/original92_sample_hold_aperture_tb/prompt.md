Given a voltage-domain sample-and-hold DUT with a nonzero aperture offset,
generate a minimal EVAS-compatible Spectre `.scs` testbench that drives
clocked sampling against a changing analog input and saves the waveforms needed
to inspect capture timing.

This is a testbench-generation task. Do not generate Verilog-A modules. Assume
the DUT Verilog-A file is provided by the benchmark harness and only write the
Spectre testbench.

Return exactly one fenced code block tagged `spectre`. Do not include prose
outside the code block.

## Provided DUT

- Include file: `sample_hold_aperture_ref.va`
- Module name: `sample_hold_aperture_ref`
- Positional port order: `(VDD, VSS, clk, vin, vout)`
- Required instance line:
  `XDUT (VDD VSS clk vin vout) sample_hold_aperture_ref`

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Provide `VDD=0.9 V` and `VSS=0 V`.
- Drive `clk` with repeated rising edges throughout the run.
- Drive `vin` with a changing analog waveform so aperture timing can be
  observed at sample edges.
- Use exactly one transient analysis:
  `tran tran stop=140n maxstep=100p`
- Save the public waveform columns:
  `save vin clk vout`
- Place the DUT include last:
  `ahdl_include "sample_hold_aperture_ref.va"`

## Public Evaluation Contract

The evaluator reads `vin`, `clk`, and `vout` from `tran.csv`. Use plain scalar
save names; do not rely on instance-qualified or aliased save names.
