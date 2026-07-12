# Single ADC 7b Weighted Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Single ADC 7b Weighted` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `single_adc_7b_weighted.va`:
  - Module `single_adc_7b_weighted` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `din4` (input, electrical)
    - position 5: `din5` (input, electrical)
    - position 6: `din6` (input, electrical)
    - position 7: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `single_adc_7b_weighted` as `XDUT` with ordered public binding: din0=din0, din1=din1, din2=din2, din3=din3, din4=din4, din5=din5, din6=din6, dout=dout.

## Public Parameter Contract

- `single_adc_7b_weighted.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INPUT_THRESHOLDING`: exercise and make observable: Treat each `din` input as high only when it is above `vth`. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_WEIGHTED_CODE_SUM`: exercise and make observable: Sum the selected 7-bit weights, including the MSB contribution, using the declared weight basis. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_NORMALIZED_SINGLE_ENDED_OUTPUT`: exercise and make observable: Drive the normalized single-ended ADC output from the weighted code without extra fixed offsets or scale errors. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_MONOTONIC_CODE_RESPONSE`: exercise and make observable: The output changes monotonically with increasing selected code weight. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.

The required trace names are: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
