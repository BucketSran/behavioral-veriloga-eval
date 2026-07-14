# Pipe15 Data Align Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Pipe15 Data Align` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pipe15_data_align.va`:
  - Module `pipe15_data_align` (entry)
    - position 0: `samp` (input, electrical)
    - position 1: `d0` (input, electrical)
    - position 2: `d1` (input, electrical)
    - position 3: `d2` (input, electrical)
    - position 4: `d3` (input, electrical)
    - position 5: `d4` (input, electrical)
    - position 6: `d5` (input, electrical)
    - position 7: `d6` (input, electrical)
    - position 8: `d7` (input, electrical)
    - position 9: `d8` (input, electrical)
    - position 10: `d9` (input, electrical)
    - position 11: `d10` (input, electrical)
    - position 12: `d11` (input, electrical)
    - position 13: `d12` (input, electrical)
    - position 14: `d13` (input, electrical)
    - position 15: `d14` (input, electrical)
    - position 16: `do0` (output, electrical)
    - position 17: `do1` (output, electrical)
    - position 18: `do2` (output, electrical)
    - position 19: `do3` (output, electrical)
    - position 20: `do4` (output, electrical)
    - position 21: `do5` (output, electrical)
    - position 22: `do6` (output, electrical)
    - position 23: `do7` (output, electrical)
    - position 24: `do8` (output, electrical)
    - position 25: `do9` (output, electrical)
    - position 26: `do10` (output, electrical)
    - position 27: `do11` (output, electrical)
    - position 28: `do12` (output, electrical)
    - position 29: `do13` (output, electrical)
    - position 30: `do14` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pipe15_data_align` as `XDUT` with ordered public binding: samp=samp, d0=d0, d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6, d7=d7, d8=d8, d9=d9, d10=d10, d11=d11, d12=d12, d13=d13, d14=d14, do0=do0, do1=do1, do2=do2, do3=do3, do4=do4, do5=do5, do6=do6, do7=do7, do8=do8, do9=do9, do10=do10, do11=do11, do12=do12, do13=do13, do14=do14.

## Public Parameter Contract

- `pipe15_data_align.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pipe15_data_align.tt` defaults to `20p`; valid range: finite; overrides tt.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLE_ON_RISING_SAMP`: exercise and make observable: On each rising `samp` crossing, sample all fifteen input bits `d0..d14` into the alignment pipeline. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_ZERO_DELAY_OUTPUT_GROUP`: exercise and make observable: Outputs `do0..do2` publish the current sampled values without an added sample delay. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_STAGGERED_DELAY_OUTPUT_GROUPS`: exercise and make observable: Outputs `do3..do6`, `do7..do10`, and `do11..do14` publish the one-, two-, and three-sample delayed input groups respectively. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.
- `P_VOLTAGE_CODED_OUTPUT_LEVELS`: exercise and make observable: Every aligned output is driven as a voltage-coded logic level near 0 V or `vdd` with the declared transition timing. Required traces: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.

The required trace names are: `time`, `d0`, `d1`, `d10`, `d11`, `d12`, `d13`, `d14`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `do0`, `do1`, `do10`, `do11`, `do12`, `do13`, `do14`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`, `do9`, `samp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
