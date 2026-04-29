Write a Verilog-A module named `d2b_4bit` and a minimal EVAS-compatible
Spectre testbench for it.

Return exactly two fenced code blocks:

1. A `verilog-a` block for module `d2b_4bit`
2. A `spectre` block for the testbench

Do not include prose outside the code blocks.

## DUT Contract

- Module name: `d2b_4bit`
- Positional port order: `(VDD, VSS, VIN, DOUT3, DOUT2, DOUT1, DOUT0)`
- All ports are electrical.
- `VDD` and `VSS` are supply rails.
- `VIN` is a continuous analog input over the `VSS` to `VDD` range.
- `DOUT3` is the MSB and `DOUT0` is the LSB.

## Behavioral Intent

- Implement a static 4-bit analog-to-binary converter.
- The output code should increase monotonically as `VIN` increases.
- Clip the code to the range `[0, 15]`.
- Drive each output bit as a voltage level using `transition(...)`.
- Use pure, Spectre-compatible Verilog-A syntax.

## Required Testbench Structure

- Start with `simulator lang=spectre` and `global 0`.
- Include the generated DUT file:
  `ahdl_include "d2b_4bit.va"`
- Provide `vdd=0.9 V` and `vss=0 V`.
- Drive `vin` with a monotonic ramp from 0 V to 0.9 V over the run.
- Instantiate the DUT by position:
  `IDUT (vdd vss vin DOUT3 DOUT2 DOUT1 DOUT0) d2b_4bit`
- Use exactly one transient analysis:
  `tran tran stop=100n maxstep=2n`
- Save the public waveform columns:
  `save vin DOUT3 DOUT2 DOUT1 DOUT0`

## Public Evaluation Contract

The evaluator reads the transient waveform columns `vin`, `DOUT3`, `DOUT2`,
`DOUT1`, and `DOUT0`. Use plain scalar save names; do not rely on
instance-qualified or aliased save names.
