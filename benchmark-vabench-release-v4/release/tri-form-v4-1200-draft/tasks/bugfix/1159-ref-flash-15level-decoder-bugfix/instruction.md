# Ref Flash 15level Decoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `ref_flash_15level_decoder.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ref_flash_15level_decoder.tt` defaults to `10p`; valid range: finite; overrides tt.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_FIFTEEN_TAP_COUNT`: restore: Each rising `clks` crossing counts voltage-coded assertions across the 15 tap inputs. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.
- `P_FULL_TAP_COVERAGE`: restore: Upper and lower tap inputs all contribute to the count; no subset of taps is ignored. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.
- `P_FRACTION_NORMALIZATION_AND_GAIN`: restore: `dout` reports the count divided by 15 without additional gain scaling. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt10`, `dt11`, `dt12`, `dt13`, `dt14`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `dt8`, `dt9`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ref_flash_15level_decoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
