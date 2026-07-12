# DAC Restore 10bit Offset Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DAC Restore 10bit Offset` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_restore_10bit_offset.va`:
  - Module `dac_restore_10bit_offset` (entry)
    - position 0: `D1` (input, electrical)
    - position 1: `D2` (input, electrical)
    - position 2: `D3` (input, electrical)
    - position 3: `D4` (input, electrical)
    - position 4: `D5` (input, electrical)
    - position 5: `D6` (input, electrical)
    - position 6: `D7` (input, electrical)
    - position 7: `D8` (input, electrical)
    - position 8: `D9` (input, electrical)
    - position 9: `D10` (input, electrical)
    - position 10: `D0` (input, electrical)
    - position 11: `clk` (input, electrical)
    - position 12: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_restore_10bit_offset` as `XDUT` with ordered public binding: D1=d1, D2=d2, D3=d3, D4=d4, D5=d5, D6=d6, D7=d7, D8=d8, D9=d9, D10=d10, D0=d0, clk=clk, vout=vout.

## Public Parameter Contract

- `dac_restore_10bit_offset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dac_restore_10bit_offset.lsb` defaults to `1.8 / 1024.0`; valid range: finite; overrides lsb.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_CODE_SAMPLING`: exercise and make observable: Only rising crossings of `clk` through `vth` update the held DAC output; input-bit changes between clock crossings do not alter `vout`. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_WEIGHTED_REDUNDANT_CODE`: exercise and make observable: `D10` is the largest weight, `D0` is the LSB, and `D6` and `D7` both contribute the redundant 64-LSB weight before scaling. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_OFFSET_MIDRISE_OUTPUT`: exercise and make observable: The asserted weighted code is shifted by the source -32 LSB offset and placed at the mid-rise half-LSB output level using the public `lsb` scale. Required traces: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.
- `P_OUTPUT_SMOOTH_HOLD`: exercise and make observable: `vout` transitions smoothly to each sampled code value and holds that value until the next qualifying clock edge. Required traces: `time`, `clk`, `vout`.

The required trace names are: `time`, `clk`, `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `D8`, `D9`, `D10`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
