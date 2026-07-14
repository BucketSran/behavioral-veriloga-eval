# Resettable DAC Restore 7bit Clocked Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Resettable DAC Restore 7bit Clocked` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_restore_7bit_clocked.va`:
  - Module `dac_restore_7bit_clocked` (entry)
    - position 0: `d6` (input, electrical)
    - position 1: `d5` (input, electrical)
    - position 2: `d4` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `d2` (input, electrical)
    - position 5: `d1` (input, electrical)
    - position 6: `d0` (input, electrical)
    - position 7: `clk` (input, electrical)
    - position 8: `rst` (input, electrical)
    - position 9: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_restore_7bit_clocked` as `XDUT` with ordered public binding: d6=d6, d5=d5, d4=d4, d3=d3, d2=d2, d1=d1, d0=d0, clk=clk, rst=rst, vout=vout.

## Public Parameter Contract

- `dac_restore_7bit_clocked.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_WHEN_RST_RISES_ABOVE_THRESHOLD_IMMEDIATELY`: exercise and make observable: When `rst` rises above threshold, immediately restore `vout` to the midscale value of 0 V. While `rst` remains high, ignore clock edges and hold the restored midscale value. When `rst` is low, each rising `clk` crossing decodes `d6..d0` as a 7-bit binary word and drives `vout` to the center of that code bin across a bipolar 1.8 V span from `-0.9 V` to `+0.9 V`. Hold the output between clock events. Required traces: `time`, `clk`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `rst`, `vout`.

The required trace names are: `time`, `clk`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `rst`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
