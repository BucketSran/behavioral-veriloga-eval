# Flash Data Align Pipeline Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Flash Data Align Pipeline` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `flash_data_align_pipeline.va`:
  - Module `flash_data_align_pipeline` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `din0` (input, electrical)
    - position 2: `din1` (input, electrical)
    - position 3: `din2` (input, electrical)
    - position 4: `din3` (input, electrical)
    - position 5: `din4` (input, electrical)
    - position 6: `din5` (input, electrical)
    - position 7: `din6` (input, electrical)
    - position 8: `din7` (input, electrical)
    - position 9: `dout0` (output, electrical)
    - position 10: `dout1` (output, electrical)
    - position 11: `dout2` (output, electrical)
    - position 12: `dout3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `flash_data_align_pipeline` as `XDUT` with ordered public binding: clk=clk, din0=din0, din1=din1, din2=din2, din3=din3, din4=din4, din5=din5, din6=din6, din7=din7, dout0=dout0, dout1=dout1, dout2=dout2, dout3=dout3.

## Public Parameter Contract

- `flash_data_align_pipeline.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_THERMOMETER_COUNT`: exercise and make observable: At each rising `clk` crossing through `vth`, count all asserted thermometer inputs `din0` through `din7`. Required traces: `time`, `clk`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`.
- `P_FOUR_STAGE_ALIGNMENT`: exercise and make observable: The sampled count is shifted through a four-stage alignment pipeline before it is published. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_BINARY_OUTPUT_ORDER`: exercise and make observable: The delayed count is driven as voltage-coded binary with `dout0` as LSB and `dout3` as MSB. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_EVENT_HELD_OUTPUTS`: exercise and make observable: Outputs update only from pipeline clock events and hold their previous voltage-coded state between events. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.

The required trace names are: `time`, `clk`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`, `dout0`, `dout1`, `dout2`, `dout3`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
