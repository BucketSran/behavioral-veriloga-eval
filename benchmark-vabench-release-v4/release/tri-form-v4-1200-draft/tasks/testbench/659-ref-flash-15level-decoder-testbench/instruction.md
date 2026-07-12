# Ref Flash 15level Decoder Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Ref Flash 15level Decoder` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ref_flash_15level_decoder.va`:
  - Module `ref_flash_15level_decoder` (entry)
    - position 0: `dt0` (input, electrical)
    - position 1: `dt1` (input, electrical)
    - position 2: `dt2` (input, electrical)
    - position 3: `dt3` (input, electrical)
    - position 4: `dt4` (input, electrical)
    - position 5: `dt5` (input, electrical)
    - position 6: `dt6` (input, electrical)
    - position 7: `dt7` (input, electrical)
    - position 8: `dt8` (input, electrical)
    - position 9: `dt9` (input, electrical)
    - position 10: `dt10` (input, electrical)
    - position 11: `dt11` (input, electrical)
    - position 12: `dt12` (input, electrical)
    - position 13: `dt13` (input, electrical)
    - position 14: `dt14` (input, electrical)
    - position 15: `clks` (input, electrical)
    - position 16: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ref_flash_15level_decoder` as `XDUT` with ordered public binding: dt0=dt0, dt1=dt1, dt2=dt2, dt3=dt3, dt4=dt4, dt5=dt5, dt6=dt6, dt7=dt7, dt8=dt8, dt9=dt9, dt10=dt10, dt11=dt11, dt12=dt12, dt13=dt13, dt14=dt14, clks=clks, dout=dout.

## Public Parameter Contract

- `ref_flash_15level_decoder.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ref_flash_15level_decoder.tt` defaults to `10p`; valid range: finite; overrides tt.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_FIFTEEN_TAP_COUNT`: exercise and make observable: Each rising `clks` crossing counts voltage-coded assertions across the 15 tap inputs. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.
- `P_FULL_TAP_COVERAGE`: exercise and make observable: Upper and lower tap inputs all contribute to the count; no subset of taps is ignored. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.
- `P_FRACTION_NORMALIZATION_AND_GAIN`: exercise and make observable: `dout` reports the count divided by 15 without additional gain scaling. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.

The required trace names are: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
