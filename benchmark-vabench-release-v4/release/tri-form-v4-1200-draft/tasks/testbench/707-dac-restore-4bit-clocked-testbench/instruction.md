# DAC Restore 4bit Clocked Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DAC Restore 4bit Clocked` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_restore_4bit_clocked.va`:
  - Module `dac_restore_4bit_clocked` (entry)
    - position 0: `d3` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d1` (input, electrical)
    - position 3: `d0` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_restore_4bit_clocked` as `XDUT` with ordered public binding: d3=d3, d2=d2, d1=d1, d0=d0, clk=clk, vout=vout.

## Public Parameter Contract

- `dac_restore_4bit_clocked.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CLK_CROSSING_DECODE`: exercise and make observable: On each rising `clk` crossing, decode `d3..d0` as a 4-bit binary word and drive `vout` to the center of that code bin across a bipolar 1.8 V span from `-0.9 V` to `+0.9 V`. Hold the output between clock events. Required traces: `time`, `clk`, `d0`, `d1`, `d2`, `d3`, `vout`.

The required trace names are: `time`, `clk`, `d0`, `d1`, `d2`, `d3`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
