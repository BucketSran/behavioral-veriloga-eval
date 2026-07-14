# DAC Restore 6bit 1p8 Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DAC Restore 6bit 1p8` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_restore_6bit_1p8.va`:
  - Module `dac_restore_6bit_1p8` (entry)
    - position 0: `d1` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d3` (input, electrical)
    - position 3: `d4` (input, electrical)
    - position 4: `d5` (input, electrical)
    - position 5: `d6` (input, electrical)
    - position 6: `clk` (input, electrical)
    - position 7: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_restore_6bit_1p8` as `XDUT` with ordered public binding: d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6, clk=clk, vout=vout.

## Public Parameter Contract

- `dac_restore_6bit_1p8.vth` defaults to `0.9`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CROSSING_OF_CLK`: exercise and make observable: On each rising crossing of `clk` through `vth`, sample `d1..d6` and decode an unsigned 6-bit code with weights `32, 16, 8, 4, 2, 1`. Hold the decoded output until the next rising clock event. Map the sampled code to a bipolar 1.8 V mid-rise level: Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.
- `P_TEXT_VOUT_CODE_0_5_3`: exercise and make observable: ```text vout = (code + 0.5) * 3.6 / 64 - 1.8 ``` Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.
- `P_THE_ALL_ZERO_CODE_THEREFORE_PRODUCES`: exercise and make observable: The all-zero code therefore produces the lowest half-LSB-centered negative level, and the all-one code produces the highest half-LSB-centered positive level. Required traces: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.

The required trace names are: `time`, `clk`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
