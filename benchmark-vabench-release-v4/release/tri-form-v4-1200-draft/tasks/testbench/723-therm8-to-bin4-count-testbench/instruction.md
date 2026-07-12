# Therm8 To Bin4 Count Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Therm8 To Bin4 Count` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `therm8_to_bin4_count.va`:
  - Module `therm8_to_bin4_count` (entry)
    - position 0: `th0` (input, electrical)
    - position 1: `th1` (input, electrical)
    - position 2: `th2` (input, electrical)
    - position 3: `th3` (input, electrical)
    - position 4: `th4` (input, electrical)
    - position 5: `th5` (input, electrical)
    - position 6: `th6` (input, electrical)
    - position 7: `th7` (input, electrical)
    - position 8: `b0` (output, electrical)
    - position 9: `b1` (output, electrical)
    - position 10: `b2` (output, electrical)
    - position 11: `b3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `therm8_to_bin4_count` as `XDUT` with ordered public binding: th0=th0, th1=th1, th2=th2, th3=th3, th4=th4, th5=th5, th6=th6, th7=th7, b0=b0, b1=b1, b2=b2, b3=b3.

## Public Parameter Contract

- `therm8_to_bin4_count.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_COUNT_HOW_MANY_OF_TH0_TH7`: exercise and make observable: Count how many of `th0..th7` are above `vth`. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_ENCODE_THE_COUNT_AS_A_4`: exercise and make observable: Encode the count as a 4-bit binary word. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_DRIVE_B0_B3_AS_VOLTAGE_CODED`: exercise and make observable: Drive `b0..b3` as voltage-coded outputs with `b0` as the least significant bit. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.
- `P_SUPPORT_ANY_INPUT_PATTERN_BY_COUNTING`: exercise and make observable: Support any input pattern by counting high inputs rather than assuming a perfectly monotonic thermometer prefix. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.

The required trace names are: `time`, `b0`, `b1`, `b2`, `b3`, `th0`, `th1`, `th2`, `th3`, `th4`, `th5`, `th6`, `th7`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
