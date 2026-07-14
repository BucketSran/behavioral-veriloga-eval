# Ref Flash 8level Decoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ref_flash_8level_decoder.va`:
  - Module `ref_flash_8level_decoder` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `dt0` (input, electrical)
    - position 2: `dt1` (input, electrical)
    - position 3: `dt2` (input, electrical)
    - position 4: `dt3` (input, electrical)
    - position 5: `dt4` (input, electrical)
    - position 6: `dt5` (input, electrical)
    - position 7: `dt6` (input, electrical)
    - position 8: `dt7` (input, electrical)
    - position 9: `clks` (input, electrical)
    - position 10: `dout` (output, electrical)
    - position 11: `vres` (output, electrical)

## Public Parameter Contract

- `ref_flash_8level_decoder.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ref_flash_8level_decoder.tt` defaults to `10p`; valid range: finite; overrides tt.
- `ref_flash_8level_decoder.vref` defaults to `1`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_EIGHT_TAP_COUNT`: restore: Each rising `clks` crossing counts all eight asserted flash taps into the held decoder count. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `vin`, `vres`.
- `P_RESIDUE_CENTERING`: restore: `vres` subtracts the centered four-count flash estimate from the sampled input residue. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `vin`, `vres`.
- `P_OUTPUT_NORMALIZATION`: restore: `dout` reports the tap count normalized by eight without extra output scaling. Required traces: `time`, `clks`, `dout`, `dt0`, `dt1`, `dt2`, `dt3`, `dt4`, `dt5`, `dt6`, `dt7`, `vin`, `vres`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ref_flash_8level_decoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
