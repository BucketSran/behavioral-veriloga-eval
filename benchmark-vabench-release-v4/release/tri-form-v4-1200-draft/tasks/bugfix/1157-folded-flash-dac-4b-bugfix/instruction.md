# Folded Flash DAC 4b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `folded_flash_dac_4b.va`:
  - Module `folded_flash_dac_4b` (entry)
    - position 0: `vd4` (input, electrical)
    - position 1: `vd3` (input, electrical)
    - position 2: `vd2` (input, electrical)
    - position 3: `vd1` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- `folded_flash_dac_4b.vref` defaults to `1 from [0:inf]`; valid range: finite; overrides vref.
- `folded_flash_dac_4b.trise` defaults to `1p from [0:inf]`; valid range: finite; overrides trise.
- `folded_flash_dac_4b.tfall` defaults to `1p from [0:inf]`; valid range: finite; overrides tfall.
- `folded_flash_dac_4b.tdel` defaults to `0 from [0:inf]`; valid range: finite; overrides tdel.
- `folded_flash_dac_4b.vtrans` defaults to `0.45`; valid range: finite; overrides vtrans.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_VOLTAGE_CODED_SUBCODE_DECODE`: restore: `vd1` through `vd3` form the lower subcode and `vd4` selects the folded branch using `vtrans`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_FOLD_MIRROR_TRANSFER`: restore: The upper folded branch mirrors the subcode around the fold center instead of using a direct unsigned code. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_OUTPUT_SCALE_DENOMINATOR`: restore: The folded code is scaled by the declared 4-bit denominator and reference before driving `vout`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `folded_flash_dac_4b.va`.
Every supplied `.va` file is editable; do not add or omit files.
